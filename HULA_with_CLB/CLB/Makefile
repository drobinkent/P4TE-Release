p4-leaf-ecmp: p4src/src/leaf.p4
	$(info *** Building P4 program for the leaf switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/leaf.json \
		--p4runtime-files p4src/Build/leaf_p4info.txt --Wdisable=unsupported \
		p4src/src/leaf.p4 -Dports=256 -DENABLE_DEBUG_TABLES -DDP_ALGO_ECMP -DECN_ENABLED -DBITMASK_LENGTH=16  -DBITMASK_POSITION_INDICATOR_BITS_LENGTH=4  -DPRECISION_FACTOR=3
	sudo cp ./p4src/Build/leaf.json /tmp/
	sudo cp ./p4src/Build/leaf_p4info.txt /tmp/
	@echo "*** P4 program for leaf switch compiled successfully! Output files are in p4src/Build"

p4-spine-ecmp: p4src/src/spine.p4
	$(info *** Building P4 program for the spine switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/spine.json \
		--p4runtime-files p4src/Build/spine_p4info.txt --Wdisable=unsupported \
		p4src/src/spine.p4 -Dports=256  -DENABLE_DEBUG_TABLES -DDP_ALGO_ECMP -DECN_ENABLED -DBITMASK_LENGTH=16  -DBITMASK_POSITION_INDICATOR_BITS_LENGTH=4  -DPRECISION_FACTOR=3
	sudo cp ./p4src/Build/spine.json /tmp/
	sudo cp ./p4src/Build/spine_p4info.txt /tmp/
	@echo "*** P4 program for spine switch compiled successfully! Output files are in p4src/Build"

p4-ecmp: p4-leaf-ecmp p4-spine-ecmp
	$(info *** Building P4 program with ECMP routing for the leaf and spine switch...)


p4-leaf-clb: p4src/src/leaf.p4
	$(info *** Building P4 program for the leaf switch for CLB...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/leaf.json \
		--p4runtime-files p4src/Build/leaf_p4info.txt --Wdisable=unsupported \
		p4src/src/leaf.p4 -Dports=256 -DENABLE_DEBUG_TABLES -DDP_ALGO_CLB  -DBITMASK_LENGTH=16  -DBITMASK_POSITION_INDICATOR_BITS_LENGTH=4  -DPRECISION_FACTOR=3
	sudo cp ./p4src/Build/leaf.json /tmp/
	sudo cp ./p4src/Build/leaf_p4info.txt /tmp/
	@echo "*** P4 program for leaf switch compiled successfully! Output files are in p4src/Build"

p4-spine-clb: p4src/src/spine.p4
	$(info *** Building P4 program for the spine switch...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/spine.json \
		--p4runtime-files p4src/Build/spine_p4info.txt --Wdisable=unsupported \
		p4src/src/spine.p4 -Dports=256  -DENABLE_DEBUG_TABLES  -DBITMASK_LENGTH=16  -DBITMASK_POSITION_INDICATOR_BITS_LENGTH=4  -DPRECISION_FACTOR=3
	sudo cp ./p4src/Build/spine.json /tmp/
	sudo cp ./p4src/Build/spine_p4info.txt /tmp/
	@echo "*** P4 program for spine switch compiled successfully! Output files are in p4src/Build"

p4-clb: p4-leaf-clb p4-spine-clb
	$(info *** Building P4 program with CLB load balancing for the leaf and spine switch...)


p4-leaf-hula: p4src/src/leaf.p4
	$(info *** Building P4 program for the leaf switch for hula...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/leaf.json \
		--p4runtime-files p4src/Build/leaf_p4info.txt --Wdisable=unsupported \
		p4src/src/leaf.p4 -Dports=256 -DENABLE_DEBUG_TABLES -DDP_ALGO_HULA -DBITMASK_LENGTH=16  -DBITMASK_POSITION_INDICATOR_BITS_LENGTH=4  -DPRECISION_FACTOR=3
	sudo cp ./p4src/Build/leaf.json /tmp/
	sudo cp ./p4src/Build/leaf_p4info.txt /tmp/
	@echo "*** P4 program for leaf switch compiled successfully! Output files are in p4src/Build"

p4-spine-hula: p4src/src/spine.p4
	$(info *** Building P4 program for the spine switch for hula...)
	@mkdir -p p4src/Build
	p4c-bm2-ss --arch v1model -o p4src/Build/spine.json \
		--p4runtime-files p4src/Build/spine_p4info.txt --Wdisable=unsupported \
		p4src/src/spine.p4 -Dports=256  -DENABLE_DEBUG_TABLES  -DDP_ALGO_HULA -DBITMASK_LENGTH=16  -DBITMASK_POSITION_INDICATOR_BITS_LENGTH=4  -DPRECISION_FACTOR=3
	sudo cp ./p4src/Build/spine.json /tmp/
	sudo cp ./p4src/Build/spine_p4info.txt /tmp/
	@echo "*** P4 program for spine switch compiled successfully! Output files are in p4src/Build"

p4-hula: p4-leaf-hula p4-spine-hula
	$(info *** Building P4 program with CLB load balancing for the leaf and spine switch for hula...)

start_clos: MininetSimulator/clos.py
	$(info *** Starting clos topology DCN using MininetSimulator/clos.py...)
	sudo  python3 -E MininetSimulator/clos.py

start_ctrlr: Mycontroller.py
	$(info *** Starting Mycontroller...)
	rm -rf log/controller.log
	python3 Mycontroller.py


clear-logs:
	sudo rm -rf /tmp/*
	rm -rf testAndMeasurement/TEST_LOG/*
	rm -rf result/*
	rm -rf log/*
	rm -rf result/*
	sudo pkill -f iperf

clear-iperf-processes:
	sudo pkill -f iperf

count-iperf-processes:
	ps -aux | grep -c "iperf"





generate-p4c-graphs:
	p4c-graphs --arch v1model --Wdisable=unsupported p4src/src/leaf.p4 -DENABLE_DEBUG_TABLES -DDP_ALGO_CLB  -DBITMASK_LENGTH=16  -DBITMASK_POSITION_INDICATOR_BITS_LENGTH=4  -DPRECISION_FACTOR=1  --graphs-dir p4src/graphs/leaf
	dot -Tpng p4src/graphs/leaf/IngressPipeImpl.dot > p4src/graphs/leaf/IngressPipeImpl.png