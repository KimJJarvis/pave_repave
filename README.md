# Pave Repave Proceedure

The Pave Repave Proceedure replaces peer in a NMS cluster.

The peer must be an active node in the NMS cluster and it must have a HSA as its secondary.  The peer node will be replaced by a stand alone spare node.  When the proceedure is complete, the spare node will be the active peer in the NMS cluster, the original HSA will be its secondary and the original peer will be a stand alone spare.



