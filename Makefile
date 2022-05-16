p4-leaf-ecmp: p4src/src/leaf.p4
	$(info *** Building P4 program for the leaf switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/leaf.json \
		--p4runtime-files p4src/Build/leaf_p4info.txt --Wdisable=unsupported \
		p4src/src/leaf.p4 -Dports=256 -DENABLE_DEBUG_TABLES -DDP_ALGO_ECMP -DECN_ENABLED
	sudo cp ./p4src/Build/leaf.json /tmp/
	sudo cp ./p4src/Build/leaf_p4info.txt /tmp/
	@echo "*** P4 program for leaf switch compiled successfully! Output files are in p4src/Build"

p4-spine-ecmp: p4src/src/spine.p4
	$(info *** Building P4 program for the spine switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/spine.json \
		--p4runtime-files p4src/Build/spine_p4info.txt --Wdisable=unsupported \
		p4src/src/spine.p4 -Dports=256  -DENABLE_DEBUG_TABLES -DDP_ALGO_ECMP -DECN_ENABLED
	sudo cp ./p4src/Build/spine.json /tmp/
	sudo cp ./p4src/Build/spine_p4info.txt /tmp/
	@echo "*** P4 program for spine switch compiled successfully! Output files are in p4src/Build"

p4-ecmp: p4-leaf-ecmp p4-spine-ecmp
	$(info *** Building P4 program with ECMP routing for the leaf and spine switch...)


p4-leaf-cp-assisted-multicriteria-policy-routing-without-rate-control: p4src/src/leaf.p4
	$(info *** Building P4 program for the leaf switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/leaf.json \
		--p4runtime-files p4src/Build/leaf_p4info.txt --Wdisable=unsupported \
		p4src/src/leaf.p4 -Dports=256 -DENABLE_DEBUG_TABLES -DDP_ALGO_CP_ASSISTED_POLICY_ROUTING
	sudo cp ./p4src/Build/leaf.json /tmp/
	sudo cp ./p4src/Build/leaf_p4info.txt /tmp/
	@echo "*** P4 program for leaf switch compiled successfully! Output files are in p4src/Build"

p4-spine-cp-assisted-multicriteria-policy-routing-without-rate-control: p4src/src/spine.p4
	$(info *** Building P4 program for the spine switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/spine.json \
		--p4runtime-files p4src/Build/spine_p4info.txt --Wdisable=unsupported \
		p4src/src/spine.p4 -Dports=256  -DENABLE_DEBUG_TABLES -DDP_ALGO_CP_ASSISTED_POLICY_ROUTING
	sudo cp ./p4src/Build/spine.json /tmp/
	sudo cp ./p4src/Build/spine_p4info.txt /tmp/
	@echo "*** P4 program for spine switch compiled successfully! Output files are in p4src/Build"

p4-cp-assisted-multicriteria-policy-routing-without-rate-control: p4-leaf-cp-assisted-multicriteria-policy-routing-without-rate-control p4-spine-cp-assisted-multicriteria-policy-routing-without-rate-control
	$(info *** Building P4 program with CP assisted multicriteria policy based routing -without-rate-control for the leaf and spine switch...)

p4-leaf-cp-assisted-multicriteria-policy-routing-with-path-reveirication--without-rate-control: p4src/src/leaf.p4
	$(info *** Building P4 program for the leaf switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/leaf.json \
		--p4runtime-files p4src/Build/leaf_p4info.txt --Wdisable=unsupported \
		p4src/src/leaf.p4 -Dports=256 -DENABLE_DEBUG_TABLES -DDP_ALGO_CP_ASSISTED_POLICY_ROUTING -DPATH_REVERIFICATION_ENABLED
	sudo cp ./p4src/Build/leaf.json /tmp/
	sudo cp ./p4src/Build/leaf_p4info.txt /tmp/
	@echo "*** P4 program for leaf switch compiled successfully! Output files are in p4src/Build"

p4-spine-cp-assisted-multicriteria-policy-routing-with-path-reveirication-without-rate-control: p4src/src/spine.p4
	$(info *** Building P4 program for the spine switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/spine.json \
		--p4runtime-files p4src/Build/spine_p4info.txt --Wdisable=unsupported \
		p4src/src/spine.p4 -Dports=256  -DENABLE_DEBUG_TABLES -DDP_ALGO_CP_ASSISTED_POLICY_ROUTING -DPATH_REVERIFICATION_ENABLED
	sudo cp ./p4src/Build/spine.json /tmp/
	sudo cp ./p4src/Build/spine_p4info.txt /tmp/
	@echo "*** P4 program for spine switch compiled successfully! Output files are in p4src/Build"

p4-cp-assisted-multicriteria-policy-routing-with-path-reveirication-without-rate-control: p4-leaf-cp-assisted-multicriteria-policy-routing-with-path-reveirication-without-rate-control p4-spine-cp-assisted-multicriteria-policy-routing-with-path-reveirication-without-rate-control
	$(info *** Building P4 program with CP assisted multicriteria policy based routing -with-path-reveirication but -without-rate-control for the leaf and spine switch...)



p4-leaf-cp-assisted-multicriteria-policy-routing-with-rate-control: p4src/src/leaf.p4
	$(info *** Building P4 program for the leaf switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/leaf.json \
		--p4runtime-files p4src/Build/leaf_p4info.txt --Wdisable=unsupported \
		p4src/src/leaf.p4 -Dports=256  -DDP_ALGO_CP_ASSISTED_POLICY_ROUTING -DDP_BASED_RATE_CONTROL_ENABLED #-DENABLE_DEBUG_TABLES
	sudo cp ./p4src/Build/leaf.json /tmp/
	sudo cp ./p4src/Build/leaf_p4info.txt /tmp/
	@echo "*** P4 program for leaf switch compiled successfully! Output files are in p4src/Build"

p4-spine-cp-assisted-multicriteria-policy-routing-with-rate-control: p4src/src/spine.p4
	$(info *** Building P4 program for the spine switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/spine.json \
		--p4runtime-files p4src/Build/spine_p4info.txt --Wdisable=unsupported \
		p4src/src/spine.p4 -Dports=256   -DDP_ALGO_CP_ASSISTED_POLICY_ROUTING -DDP_BASED_RATE_CONTROL_ENABLED #-DENABLE_DEBUG_TABLES
	sudo cp ./p4src/Build/spine.json /tmp/
	sudo cp ./p4src/Build/spine_p4info.txt /tmp/
	@echo "*** P4 program for spine switch compiled successfully! Output files are in p4src/Build"

p4-cp-assisted-multicriteria-policy-routing-with-rate-control: p4-leaf-cp-assisted-multicriteria-policy-routing-with-rate-control p4-spine-cp-assisted-multicriteria-policy-routing-with-rate-control generate-p4c-graphs
	$(info *** Building P4 program with CP assisted multicriteria policy based routing -with-rate-control for the leaf and spine switch...)


p4-leaf-dp-only-multicriteria-policy-routing: p4src/src/leaf.p4
	$(info *** Building P4 program for the leaf switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/leaf.json \
		--p4runtime-files p4src/Build/leaf_p4info.txt --Wdisable=unsupported \
		p4src/src/leaf.p4 -Dports=256 -DENABLE_DEBUG_TABLES -DDP_ALGO_DP_ONLY_POLICY_ROUTING
	sudo cp ./p4src/Build/leaf.json /tmp/
	sudo cp ./p4src/Build/leaf_p4info.txt /tmp/
	@echo "*** P4 program for leaf switch compiled successfully! Output files are in p4src/Build"

p4-spine-dp-only-multicriteria-policy-routing: p4src/src/spine.p4
	$(info *** Building P4 program for the spine switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/spine.json \
		--p4runtime-files p4src/Build/spine_p4info.txt --Wdisable=unsupported \
		p4src/src/spine.p4 -Dports=256  -DENABLE_DEBUG_TABLES -DDP_ALGO_DP_ONLY_POLICY_ROUTING
	sudo cp ./p4src/Build/spine.json /tmp/
	sudo cp ./p4src/Build/spine_p4info.txt /tmp/
	@echo "*** P4 program for spine switch compiled successfully! Output files are in p4src/Build"

p4-dp-only-multicriteria-policy-routing: p4-leaf-dp-only-multicriteria-policy-routing p4-spine-dp-only-multicriteria-policy-routing
	$(info *** Building P4 program with dp only multicriteria policy based routing for the leaf and spine switch...)

start_clos: MininetSimulator/clos.py
	$(info *** Starting clos topology DCN using MininetSimulator/clos.py...)
	sudo  python3 -E MininetSimulator/clos.py

start_ctrlr: Mycontroller.py
	$(info *** Starting Mycontroller...)
	rm -rf log/controller.log
	python3 Mycontroller.py


clear-logs:
	rm -rf testAndMeasurement/TEST_LOG/*
	rm -rf result/*
	rm -rf log/*
	rm -rf result/*
	rm -rf ./MininetSimulator/TEST_LOG/*
	sudo pkill -f iperf

clear-iperf-processes:
	sudo pkill -f iperf

count-iperf-processes:
	ps -aux | grep -c "iperf"


process-l2strideSmallLarge-48kFlowRate1-2MFlowSize:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2strideSmallLarge-48kFlowRate1-2MFlowSize testAndMeasurement/TEST_RESULTS/P4TE/l2strideSmallLarge-48kFlowRate1-2MFlowSize ECMP P4TE ./ProcessedResultImages/l2strideSmallLarge-48kFlowRate1-2MFlowSize

process-l2strideSmallLarge-48kFlowRate:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2strideSmallLarge-48kFlowRate testAndMeasurement/TEST_RESULTS/P4TE/l2strideSmallLarge-48kFlowRate ECMP P4TE ./ProcessedResultImages/l2strideSmallLarge-48kFlowRate



process-linkUtilizationTester:
	mkdir ProcessedResultImages/linkUtilizationTesterGraphs
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/linkUtilizationTester testAndMeasurement/TEST_RESULTS/P4TE/linkUtilizationTester ECMP P4TE ./ProcessedResultImages/linkUtilizationTester




process-l2highContention:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2highContention testAndMeasurement/TEST_RESULTS/P4TE/l2highContention ECMP P4TE ./ProcessedResultImages/l2highContention


process-l2incast:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2-incast testAndMeasurement/TEST_RESULTS/P4TE/l2-incast ECMP P4TE ./ProcessedResultImages/l2-incast


process-l2-congestion:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2-congestion testAndMeasurement/TEST_RESULTS/P4TE/l2-congestion ECMP P4TE ./ProcessedResultImages/l2-congestion


process-l2strideSmallLarge-UnboundedRate:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2strideSmallLarge-UnboundedRate testAndMeasurement/TEST_RESULTS/P4TE/l2strideSmallLarge-UnboundedRate ECMP P4TE ./ProcessedResultImages/l2strideSmallLarge-UnboundedRate

process-Manyl2strideSmallLarge-large-window:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/Manyl2strideSmallLarge-large-window testAndMeasurement/TEST_RESULTS/P4TE/Manyl2strideSmallLarge-large-window ECMP P4TE ./ProcessedResultImages/Manyl2strideSmallLarge-large-window

process-TooManyl2strideSmallLarge-large-window:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/TooManyl2strideSmallLarge-large-window testAndMeasurement/TEST_RESULTS/P4TE/TooManyl2strideSmallLarge-large-window ECMP P4TE ./ProcessedResultImages/TooManyl2strideSmallLarge-large-window


process-l2strideSmallLarge-sc4:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2strideSmallLarge-sc4 testAndMeasurement/TEST_RESULTS/P4TE/l2strideSmallLarge-sc4 ECMP P4TE ./ProcessedResultImages/l2strideSmallLarge-sc4


process-l2strideSmallLarge-rate48k-w-24k:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2strideSmallLarge-rate48k-w-24k testAndMeasurement/TEST_RESULTS/P4TE/l2strideSmallLarge-rate48k-w-24k ECMP P4TE ./ProcessedResultImages/l2strideSmallLarge-rate48k-w-24k


process-l2strideSmallLarge-48kFlowRate100-512FlowSize:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2strideSmallLarge-48kFlowRate100-512FlowSize testAndMeasurement/TEST_RESULTS/P4TE/l2strideSmallLarge-48kFlowRate100-512FlowSize ECMP P4TE ./ProcessedResultImages/l2strideSmallLarge-48kFlowRate100-512FlowSize

process-l2strideSmallLarge-16k-sc8:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2strideSmallLarge-16k-sc8 testAndMeasurement/TEST_RESULTS/P4TE/l2strideSmallLarge-16k-sc8 ECMP P4TE ./ProcessedResultImages/l2strideSmallLarge-16k-sc8

process-l2strideSmallLarge-16k-sc4:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2strideSmallLarge-16k-sc4 testAndMeasurement/TEST_RESULTS/P4TE/l2strideSmallLarge-16k-sc4 ECMP P4TE ./ProcessedResultImages/l2strideSmallLarge-16k-sc4

process-l2strideSmallLarge-16k-sc16:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2strideSmallLarge-16k-sc16 testAndMeasurement/TEST_RESULTS/P4TE/l2strideSmallLarge-16k-sc16 ECMP P4TE ./ProcessedResultImages/l2strideSmallLarge-16k-sc16


process-l2strideSmallLarge-48kFlowRate:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2strideSmallLarge-48kFlowRate testAndMeasurement/TEST_RESULTS/P4TE/l2strideSmallLarge-48kFlowRate ECMP P4TE ./ProcessedResultImages/l2strideSmallLarge-48kFlowRate




rocess-l2strideSmallLarge-48kFlowRate100-512FlowSize:
	$(info *** Make sure you configured the FLOW_TYPE_IDENTIFIER_BY_FLOW_VOLUME_IN_KB valus in ConfigConst  for this use case)
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/ecmp/l2strideSmallLarge-48kFlowRate100-512FlowSize testAndMeasurement/TEST_RESULTS/P4TE/l2strideSmallLarge-48kFlowRate100-512FlowSize ECMP P4TE ./ProcessedResultImages/l2strideSmallLarge-48kFlowRate100-512FlowSize



copy-fig-for-paper:
	cp ProcessedResultImages/l2strideSmallLarge-16k-sc16/FCTcomparison.pdf  ProcessedResultImages/LargeStrideFCTcomparison.pdf
	cp ProcessedResultImages/l2strideSmallLarge-16k-sc16/DataLosscomparison.pdf  ProcessedResultImages/LargeStrideDataLosscomparison.pdf
	cp ProcessedResultImages/l2strideSmallLarge-16k-sc16/RetransmissionComparison.pdf  ProcessedResultImages/LargeStrideRetransmissionComparison.pdf

	cp ProcessedResultImages/l2strideSmallLarge-16k-sc8/FCTcomparison.pdf  ProcessedResultImages/SmallStrideFCTcomparison.pdf
	cp ProcessedResultImages/l2strideSmallLarge-16k-sc8/DataLosscomparison.pdf  ProcessedResultImages/SmallStrideDataLosscomparison.pdf
	cp ProcessedResultImages/l2strideSmallLarge-16k-sc8/RetransmissionComparison.pdf  ProcessedResultImages/SmallStrideRetransmissionComparison.pdf

	cp ProcessedResultImages/l2-congestion/FCTcomparison.pdf  ProcessedResultImages/l2-congestionFCTcomparison.pdf
	cp ProcessedResultImages/l2-congestion/DataLosscomparison.pdf  ProcessedResultImages/l2-congestionDataLosscomparison.pdf
	cp ProcessedResultImages/l2-congestion/RetransmissionComparison.pdf  ProcessedResultImages/l2-congestionRetransmissionComparison.pdf

	cp ProcessedResultImages/l2-incast/FCTcomparison.pdf  ProcessedResultImages/IncastFCTcomparison.pdf
	cp ProcessedResultImages/l2-incast/DataLosscomparison.pdf  ProcessedResultImages/IncastDataLosscomparison.pdf
	cp ProcessedResultImages/l2-incast/RetransmissionComparison.pdf  ProcessedResultImages/IncastRetransmissionComparison.pdf

#	cp ProcessedResultImages/l2strideSmallLarge-48kFlowRate1-2MFlowSize/FCTcomparison.pdf  ProcessedResultImages/l2strideSmallLarge-48kFlowRate1-2MFlowSizeFCTcomparison.pdf
#	cp ProcessedResultImages/l2strideSmallLarge-48kFlowRate1-2MFlowSize/DataLosscomparison.pdf  ProcessedResultImages/l2strideSmallLarge-48kFlowRate1-2MFlowSizeDataLosscomparison.pdf
#	cp ProcessedResultImages/l2strideSmallLarge-48kFlowRate1-2MFlowSize/RetransmissionComparison.pdf  ProcessedResultImages/l2strideSmallLarge-48kFlowRate1-2MFlowSizeRetransmissionComparison.pdf
#
#	cp ProcessedResultImages/l2strideSmallLarge-48kFlowRate/FCTcomparison.pdf  ProcessedResultImages/l2strideSmallLarge-48kFlowRateFCTcomparison.pdf
#	cp ProcessedResultImages/l2strideSmallLarge-48kFlowRate/DataLosscomparison.pdf  ProcessedResultImages/l2strideSmallLarge-48kFlowRateDataLosscomparison.pdf
#	cp ProcessedResultImages/l2strideSmallLarge-48kFlowRate/RetransmissionComparison.pdf  ProcessedResultImages/l2strideSmallLarge-48kFlowRateRetransmissionComparison.pdf
#
#	cp ProcessedResultImages/l2strideSmallLarge-UnboundedRate/FCTcomparison.pdf  ProcessedResultImages/l2strideSmallLarge-UnboundedRateFCTcomparison.pdf
#	cp ProcessedResultImages/l2strideSmallLarge-UnboundedRate/DataLosscomparison.pdf  ProcessedResultImages/l2strideSmallLarge-UnboundedRateDataLosscomparison.pdf
#	cp ProcessedResultImages/l2strideSmallLarge-UnboundedRate/RetransmissionComparison.pdf  ProcessedResultImages/l2strideSmallLarge-UnboundedRateRetransmissionComparison.pdf

generate-p4c-graphs:
	p4c-graphs --arch v1model --Wdisable=unsupported p4src/src/spine.p4 -Dports=256  -DENABLE_DEBUG_TABLES -DDP_ALGO_DP_ONLY_POLICY_ROUTING --graphs-dir p4src/graphs/spine
	dot -Tpng p4src/graphs/spine/EgressPipeImpl.dot > p4src/graphs/spine/Egress.png
	dot -Tpng p4src/graphs/spine/IngressPipeImpl.dot > p4src/graphs/spine/Ingress.png
	p4c-graphs --arch v1model --Wdisable=unsupported p4src/src/leaf.p4 -Dports=256  -DENABLE_DEBUG_TABLES -DDP_ALGO_DP_ONLY_POLICY_ROUTING --graphs-dir p4src/graphs/leaf
	dot -Tpng p4src/graphs/leaf/IngressPipeImpl.dot > p4src/graphs/leaf/Ingress.png
	dot -Tpng p4src/graphs/leaf/EgressPipeImpl.dot > p4src/graphs/leaf/Egress.png


process-test:
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2highContention testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2highContention ECMP P4TE ./ProcessedResultImages/test


process-merged-result-for-statistics:
	rm -rf  testAndMeasurement/TEST_RESULTS/mergedResults/
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/ecmp
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2highContention
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2mostlyLargeFlow
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2multihighContention
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2stride4SmallLarge
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2strideSmallLarge
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2highContention/client-logs-0/
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2mostlyLargeFlow/client-logs-0/
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2multihighContention/client-logs-0/
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2stride4SmallLarge/client-logs-0/
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2strideSmallLarge/client-logs-0/
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/P4TE
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2highContention
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2mostlyLargeFlow
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2multihighContention
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2stride4SmallLarge
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2strideSmallLarge
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2highContention/client-logs-0/
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2mostlyLargeFlow/client-logs-0/
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2multihighContention/client-logs-0/
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2stride4SmallLarge/client-logs-0/
	mkdir testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2strideSmallLarge/client-logs-0/
	cp  --backup=numbered testAndMeasurement/TEST_RESULTS/ecmp/l2highContention/client-logs-*/* testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2highContention/client-logs-0/
	cp  --backup=numbered testAndMeasurement/TEST_RESULTS/ecmp/l2mostlyLargeFlow/client-logs-*/* testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2mostlyLargeFlow/client-logs-0/
	cp  --backup=numbered testAndMeasurement/TEST_RESULTS/ecmp/l2multihighContention/client-logs-*/* testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2multihighContention/client-logs-0/
	cp  --backup=numbered testAndMeasurement/TEST_RESULTS/ecmp/l2stride4SmallLarge/client-logs-*/* testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2stride4SmallLarge/client-logs-0/
	cp  --backup=numbered testAndMeasurement/TEST_RESULTS/ecmp/l2strideSmallLarge/client-logs-*/* testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2strideSmallLarge/client-logs-0/
	cp  --backup=numbered testAndMeasurement/TEST_RESULTS/P4TE/l2highContention/client-logs-*/* testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2highContention/client-logs-0/
	cp  --backup=numbered testAndMeasurement/TEST_RESULTS/P4TE/l2mostlyLargeFlow/client-logs-*/* testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2mostlyLargeFlow/client-logs-0/
	cp  --backup=numbered testAndMeasurement/TEST_RESULTS/P4TE/l2multihighContention/client-logs-*/* testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2multihighContention/client-logs-0/
	cp  --backup=numbered testAndMeasurement/TEST_RESULTS/P4TE/l2stride4SmallLarge/client-logs-*/* testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2stride4SmallLarge/client-logs-0/
	cp  --backup=numbered testAndMeasurement/TEST_RESULTS/P4TE/l2strideSmallLarge/client-logs-*/* testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2strideSmallLarge/client-logs-0/



process-l2strideSmallLarge-statistics:
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2strideSmallLarge testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2strideSmallLarge ECMP P4TE ./log/ > ./processedStatistics/l2strideSmallLarge.txt

process-l2strideSmallLarge-strideCount-4-statistics:
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2stride4SmallLarge testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2stride4SmallLarge ECMP P4TE ./log/ > ./processedStatistics/l2strideSmallLarge-strideCount-4.txt


process-l2highContention-statistics:
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2highContention testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2highContention ECMP P4TE ./log/ > ./processedStatistics/l2highContention.txt


process-l2multihighContention-statistics:
	python3 ResultProcessorExecutor.py testAndMeasurement/TEST_RESULTS/mergedResults/ecmp/l2multihighContention testAndMeasurement/TEST_RESULTS/mergedResults/P4TE/l2multihighContention ECMP P4TE ./log/ > ./processedStatistics/l2multihighContention.txt


process-statistics:
	make process-l2strideSmallLarge-statistics
	make process-l2strideSmallLarge-strideCount-4-statistics
	make process-l2highContention-statistics
	make process-l2multihighContention-statistics



create-result-folders:
	mkdir ./testAndMeasurement/TEST_RESULTS/WebSearchWorkLoad_load_factor_0.2
	mkdir ./testAndMeasurement/TEST_RESULTS/WebSearchWorkLoad_load_factor_0.4
	mkdir ./testAndMeasurement/TEST_RESULTS/WebSearchWorkLoad_load_factor_0.6
#	mkdir ./testAndMeasurement/TEST_RESULTS/WebSearchWorkLoad_load_factor_0.7
	mkdir ./testAndMeasurement/TEST_RESULTS/WebSearchWorkLoad_load_factor_0.8
#	mkdir ./testAndMeasurement/TEST_RESULTS/WebSearchWorkLoad_load_factor_1.0

create-algowise-result-folder:
	mkdir ./testAndMeasurement/TEST_RESULTS/ECMP_RESULTS
	mkdir ./testAndMeasurement/TEST_RESULTS/P4KP_RESULTS
	mkdir ./testAndMeasurement/TEST_RESULTS/HULA_RESULTS
