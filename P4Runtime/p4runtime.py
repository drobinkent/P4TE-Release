# Copyright 2019 Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from functools import wraps
import google.protobuf.text_format
from google.rpc import status_pb2, code_pb2
import grpc
import logging
import queue
import sys
import threading
import time

from p4.v1 import p4runtime_pb2
from p4.v1 import p4runtime_pb2_grpc

import logging
import logging.handlers
import  ConfigConst as ConfConst
logger = logging.getLogger('P4Runtime')
logger.handlers = []
hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)


class P4RuntimeErrorFormatException(Exception):
    def __init__(self, message):
        super().__init__(message)


# Used to iterate over the p4.Error messages in a gRPC error Status object
class P4RuntimeErrorIterator:
    def __init__(self, grpc_error):
        assert(grpc_error.code() == grpc.StatusCode.UNKNOWN)
        self.grpc_error = grpc_error

        error = None
        # The gRPC Python package does not have a convenient way to access the
        # binary details for the error: they are treated as trailing metadata.
        for meta in self.grpc_error.trailing_metadata():
            if meta[0] == "grpc-status-details-bin":
                error = status_pb2.Status()
                error.ParseFromString(meta[1])
                break
        if error is None:
            raise P4RuntimeErrorFormatException("No binary details field")

        if len(error.details) == 0:
            raise P4RuntimeErrorFormatException(
                "Binary details field has empty Any details repeated field")
        self.errors = error.details
        self.idx = 0

    def __iter__(self):
        return self

    def __next__(self):
        while self.idx < len(self.errors):
            p4_error = p4runtime_pb2.Error()
            one_error_any = self.errors[self.idx]
            if not one_error_any.Unpack(p4_error):
                raise P4RuntimeErrorFormatException(
                    "Cannot convert Any message to p4.Error")
            if p4_error.canonical_code == code_pb2.OK:
                continue
            v = self.idx, p4_error
            self.idx += 1
            return v
        raise StopIteration


# P4Runtime uses a 3-level message in case of an error during the processing of
# a write batch. This means that if we do not wrap the grpc.RpcError inside a
# custom exception, we can end-up with a non-helpful exception message in case
# of failure as only the first level will be printed. In this custom exception
# class, we extract the nested error message (one for each operation included in
# the batch) in order to print error code + user-facing message.  See P4 Runtime
# documentation for more details on error-reporting.
class P4RuntimeWriteException(Exception):
    def __init__(self, grpc_error):
        assert(grpc_error.code() == grpc.StatusCode.UNKNOWN)
        super().__init__()
        self.errors = []
        try:
            error_iterator = P4RuntimeErrorIterator(grpc_error)
            for error_tuple in error_iterator:
                self.errors.append(error_tuple)
        except P4RuntimeErrorFormatException:
            raise  # just propagate exception for now

    def __str__(self):
        message = "Error(s) during Write:\n"
        for idx, p4_error in self.errors:
            code_name = code_pb2._CODE.values_by_number[
                p4_error.canonical_code].name
            message += "\t* At index {}: {}, '{}'\n".format(
                idx, code_name, p4_error.message)
        return message


class P4RuntimeException(Exception):
    def __init__(self, grpc_error):
        super().__init__()
        self.grpc_error = grpc_error

    def __str__(self):
        message = "P4Runtime RPC error ({}): {}".format(
            self.grpc_error.code().name, self.grpc_error.details())
        return message


def parse_p4runtime_write_error(f):
    @wraps(f)
    def handle(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except grpc.RpcError as e:
            if e.code() != grpc.StatusCode.UNKNOWN:
                raise e
            raise P4RuntimeWriteException(e) from None
    return handle


def parse_p4runtime_error(f):
    @wraps(f)
    def handle(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except grpc.RpcError as e:
            raise P4RuntimeException(e) from None
    return handle


class P4RuntimeClient:
    def __init__(self, device_id, grpc_addr, election_id):
        self.device_id = device_id
        self.election_id = election_id
        self.grpc_addr = grpc_addr
        logger.debug("Connecting to device {} at {}".format(device_id, grpc_addr))

        try:
            self.channel = grpc.insecure_channel(grpc_addr)
        except Exception:
            logger.critical("Failed to connect to P4Runtime server")
            sys.exit(1)
        self.stub = p4runtime_pb2_grpc.P4RuntimeStub(self.channel)
        return



    @parse_p4runtime_error
    def get_p4info(self):
        logger.debug("Retrieving P4Info file")
        req = p4runtime_pb2.GetForwardingPipelineConfigRequest()
        req.device_id = self.device_id
        req.response_type = p4runtime_pb2.GetForwardingPipelineConfigRequest.P4INFO_AND_COOKIE
        rep = self.stub.GetForwardingPipelineConfig(req)
        return rep.config.p4info

    @parse_p4runtime_error
    def set_fwd_pipe_config(self, p4info_path, bin_path):
        logger.debug("Setting forwarding pipeline config")
        req = p4runtime_pb2.SetForwardingPipelineConfigRequest()
        req.device_id = self.device_id
        election_id = req.election_id
        election_id.high = self.election_id[0]
        election_id.low = self.election_id[1]
        req.action = p4runtime_pb2.SetForwardingPipelineConfigRequest.VERIFY_AND_COMMIT
        with open(p4info_path, 'r') as f1:
            with open(bin_path, 'rb') as f2:
                try:
                    google.protobuf.text_format.Merge(f1.read(), req.config.p4info)
                except google.protobuf.text_format.ParseError:
                    logger.info("Error when parsing P4Info")
                    raise
                req.config.p4_device_config = f2.read()
        return self.stub.SetForwardingPipelineConfig(req)

    def tear_down(self):
        if self.stream_out_q:
            logger.debug("Cleaning up stream")
            self.stream_out_q.put(None)
            self.stream_recv_thread.join()
        self.channel.close()
        del self.channel  # avoid a race condition if channel deleted when process terminates

    @parse_p4runtime_write_error
    def write(self, req):
        req.device_id = self.device_id
        election_id = req.election_id
        election_id.high = self.election_id[0]
        election_id.low = self.election_id[1]
        return self.stub.Write(req)

    @parse_p4runtime_write_error
    def write_update(self, update):
        req = p4runtime_pb2.WriteRequest()
        req.device_id = self.device_id
        election_id = req.election_id
        election_id.high = self.election_id[0]
        election_id.low = self.election_id[1]
        req.updates.extend([update])
        return self.stub.Write(req)

    # Decorator is useless here: in case of server error, the exception is raised during the
    # iteration (when next() is called).
    @parse_p4runtime_error
    def read_one(self, entity):
        req = p4runtime_pb2.ReadRequest()
        req.device_id = self.device_id
        req.entities.extend([entity])
        return self.stub.Read(req)

    @parse_p4runtime_error
    def api_version(self):
        req = p4runtime_pb2.CapabilitiesRequest()
        rep = self.stub.Capabilities(req)
        return rep.p4runtime_api_version
