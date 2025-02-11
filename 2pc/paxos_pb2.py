# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: paxos.proto
# Protobuf Python Version: 5.28.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    28,
    1,
    '',
    'paxos.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0bpaxos.proto\x12\x05paxos\"\x83\x01\n\x12TransactionRequest\x12\x0e\n\x06sender\x18\x01 \x01(\t\x12\x10\n\x08receiver\x18\x02 \x01(\t\x12\x0e\n\x06\x61mount\x18\x03 \x01(\x05\x12\x11\n\ttimestamp\x18\x04 \x01(\x03\x12\x0c\n\x04type\x18\x05 \x01(\t\x12\x1a\n\x12sender_or_receiver\x18\x06 \x01(\t\"7\n\x13TransactionResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"\x89\x01\n\x18\x43rossShardPrepareRequest\x12\x0e\n\x06sender\x18\x01 \x01(\t\x12\x10\n\x08receiver\x18\x02 \x01(\t\x12\x0e\n\x06\x61mount\x18\x03 \x01(\x05\x12\x11\n\ttimestamp\x18\x04 \x01(\x03\x12\x0c\n\x04type\x18\x05 \x01(\t\x12\x1a\n\x12sender_or_receiver\x18\x06 \x01(\t\"g\n\x19\x43rossShardPrepareResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x15\n\rballot_number\x18\x03 \x01(\x05\x12\x11\n\tserver_id\x18\x04 \x01(\x05\"\xc2\x01\n\x17\x43rossShardCommitRequest\x12\x15\n\rballot_number\x18\x01 \x01(\x05\x12\x11\n\tserver_id\x18\x02 \x01(\x05\x12\x0e\n\x06sender\x18\x03 \x01(\t\x12\x10\n\x08receiver\x18\x04 \x01(\t\x12\x0e\n\x06\x61mount\x18\x05 \x01(\x05\x12\x11\n\ttimestamp\x18\x06 \x01(\x03\x12\x0c\n\x04type\x18\x07 \x01(\t\x12\x1a\n\x12sender_or_receiver\x18\x08 \x01(\t\x12\x0e\n\x06\x63ommit\x18\t \x01(\x08\"<\n\x18\x43rossShardCommitResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"+\n\x16SetActiveStatusRequest\x12\x11\n\tis_active\x18\x01 \x01(\x08\";\n\x17SetActiveStatusResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\x12\x0f\n\x07success\x18\x02 \x01(\x08\"-\n\x17SetContactStatusRequest\x12\x12\n\nis_contact\x18\x01 \x01(\x08\"<\n\x18SetContactStatusResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\x12\x0f\n\x07success\x18\x02 \x01(\x08\"z\n\rDatastoreItem\x12\x15\n\rballot_number\x18\x01 \x01(\x05\x12\x11\n\tserver_id\x18\x02 \x01(\x05\x12.\n\x0btransaction\x18\x03 \x01(\x0b\x32\x19.paxos.TransactionRequest\x12\x0f\n\x07message\x18\x04 \x01(\t\"\x99\x01\n\x0ePrepareMessage\x12\x15\n\rballot_number\x18\x01 \x01(\x05\x12\x11\n\tserver_id\x18\x02 \x01(\x05\x12.\n\x0btransaction\x18\x03 \x01(\x0b\x32\x19.paxos.TransactionRequest\x12-\n\x0f\x64\x61tastore_items\x18\x04 \x03(\x0b\x32\x14.paxos.DatastoreItem\"\x8b\x01\n\x0ePromiseMessage\x12\x15\n\rballot_number\x18\x01 \x01(\x05\x12\x11\n\tserver_id\x18\x02 \x01(\x05\x12\x0f\n\x07message\x18\x03 \x01(\t\x12\x0f\n\x07success\x18\x04 \x01(\x08\x12-\n\x0f\x64\x61tastore_items\x18\x05 \x03(\x0b\x32\x14.paxos.DatastoreItem\"i\n\rAcceptMessage\x12\x15\n\rballot_number\x18\x01 \x01(\x05\x12\x11\n\tserver_id\x18\x02 \x01(\x05\x12.\n\x0btransaction\x18\x03 \x01(\x0b\x32\x19.paxos.TransactionRequest\"^\n\x10\x41\x63\x63\x65ptedResponse\x12\x15\n\rballot_number\x18\x01 \x01(\x05\x12\x11\n\tserver_id\x18\x02 \x01(\x05\x12\x0f\n\x07success\x18\x03 \x01(\x08\x12\x0f\n\x07message\x18\x04 \x01(\t\"i\n\rCommitMessage\x12\x15\n\rballot_number\x18\x01 \x01(\x05\x12\x11\n\tserver_id\x18\x02 \x01(\x05\x12.\n\x0btransaction\x18\x03 \x01(\x0b\x32\x19.paxos.TransactionRequest\"2\n\x0e\x43ommitResponse\x12\x0f\n\x07success\x18\x03 \x01(\x08\x12\x0f\n\x07message\x18\x04 \x01(\t\"h\n\x0c\x41\x62ortMessage\x12\x15\n\rballot_number\x18\x01 \x01(\x05\x12\x11\n\tserver_id\x18\x02 \x01(\x05\x12.\n\x0btransaction\x18\x03 \x01(\x0b\x32\x19.paxos.TransactionRequest\"\x0f\n\rAbortResponse\"#\n\x0e\x42\x61lanceRequest\x12\x11\n\tclient_id\x18\x01 \x01(\x05\"5\n\x0f\x42\x61lanceResponse\x12\x11\n\tclient_id\x18\x01 \x01(\x05\x12\x0f\n\x07\x62\x61lance\x18\x02 \x01(\x05\"\x12\n\x10\x44\x61tastoreRequest\"?\n\x11\x44\x61tastoreResponse\x12*\n\x0ctransactions\x18\x01 \x03(\x0b\x32\x14.paxos.DatastoreItem2\x92\x06\n\x12TransactionService\x12K\n\x12ProcessTransaction\x12\x19.paxos.TransactionRequest\x1a\x1a.paxos.TransactionResponse\x12V\n\x11\x43rossShardPrepare\x12\x1f.paxos.CrossShardPrepareRequest\x1a .paxos.CrossShardPrepareResponse\x12S\n\x10\x43rossShardCommit\x12\x1e.paxos.CrossShardCommitRequest\x1a\x1f.paxos.CrossShardCommitResponse\x12P\n\x0fSetActiveStatus\x12\x1d.paxos.SetActiveStatusRequest\x1a\x1e.paxos.SetActiveStatusResponse\x12S\n\x10SetContactStatus\x12\x1e.paxos.SetContactStatusRequest\x1a\x1f.paxos.SetContactStatusResponse\x12\x37\n\x07Prepare\x12\x15.paxos.PrepareMessage\x1a\x15.paxos.PromiseMessage\x12\x37\n\x06\x41\x63\x63\x65pt\x12\x14.paxos.AcceptMessage\x1a\x17.paxos.AcceptedResponse\x12\x35\n\x06\x43ommit\x12\x14.paxos.CommitMessage\x1a\x15.paxos.CommitResponse\x12\x32\n\x05\x41\x62ort\x12\x13.paxos.AbortMessage\x1a\x14.paxos.AbortResponse\x12;\n\nGetBalance\x12\x15.paxos.BalanceRequest\x1a\x16.paxos.BalanceResponse\x12\x41\n\x0cGetDatastore\x12\x17.paxos.DatastoreRequest\x1a\x18.paxos.DatastoreResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'paxos_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_TRANSACTIONREQUEST']._serialized_start=23
  _globals['_TRANSACTIONREQUEST']._serialized_end=154
  _globals['_TRANSACTIONRESPONSE']._serialized_start=156
  _globals['_TRANSACTIONRESPONSE']._serialized_end=211
  _globals['_CROSSSHARDPREPAREREQUEST']._serialized_start=214
  _globals['_CROSSSHARDPREPAREREQUEST']._serialized_end=351
  _globals['_CROSSSHARDPREPARERESPONSE']._serialized_start=353
  _globals['_CROSSSHARDPREPARERESPONSE']._serialized_end=456
  _globals['_CROSSSHARDCOMMITREQUEST']._serialized_start=459
  _globals['_CROSSSHARDCOMMITREQUEST']._serialized_end=653
  _globals['_CROSSSHARDCOMMITRESPONSE']._serialized_start=655
  _globals['_CROSSSHARDCOMMITRESPONSE']._serialized_end=715
  _globals['_SETACTIVESTATUSREQUEST']._serialized_start=717
  _globals['_SETACTIVESTATUSREQUEST']._serialized_end=760
  _globals['_SETACTIVESTATUSRESPONSE']._serialized_start=762
  _globals['_SETACTIVESTATUSRESPONSE']._serialized_end=821
  _globals['_SETCONTACTSTATUSREQUEST']._serialized_start=823
  _globals['_SETCONTACTSTATUSREQUEST']._serialized_end=868
  _globals['_SETCONTACTSTATUSRESPONSE']._serialized_start=870
  _globals['_SETCONTACTSTATUSRESPONSE']._serialized_end=930
  _globals['_DATASTOREITEM']._serialized_start=932
  _globals['_DATASTOREITEM']._serialized_end=1054
  _globals['_PREPAREMESSAGE']._serialized_start=1057
  _globals['_PREPAREMESSAGE']._serialized_end=1210
  _globals['_PROMISEMESSAGE']._serialized_start=1213
  _globals['_PROMISEMESSAGE']._serialized_end=1352
  _globals['_ACCEPTMESSAGE']._serialized_start=1354
  _globals['_ACCEPTMESSAGE']._serialized_end=1459
  _globals['_ACCEPTEDRESPONSE']._serialized_start=1461
  _globals['_ACCEPTEDRESPONSE']._serialized_end=1555
  _globals['_COMMITMESSAGE']._serialized_start=1557
  _globals['_COMMITMESSAGE']._serialized_end=1662
  _globals['_COMMITRESPONSE']._serialized_start=1664
  _globals['_COMMITRESPONSE']._serialized_end=1714
  _globals['_ABORTMESSAGE']._serialized_start=1716
  _globals['_ABORTMESSAGE']._serialized_end=1820
  _globals['_ABORTRESPONSE']._serialized_start=1822
  _globals['_ABORTRESPONSE']._serialized_end=1837
  _globals['_BALANCEREQUEST']._serialized_start=1839
  _globals['_BALANCEREQUEST']._serialized_end=1874
  _globals['_BALANCERESPONSE']._serialized_start=1876
  _globals['_BALANCERESPONSE']._serialized_end=1929
  _globals['_DATASTOREREQUEST']._serialized_start=1931
  _globals['_DATASTOREREQUEST']._serialized_end=1949
  _globals['_DATASTORERESPONSE']._serialized_start=1951
  _globals['_DATASTORERESPONSE']._serialized_end=2014
  _globals['_TRANSACTIONSERVICE']._serialized_start=2017
  _globals['_TRANSACTIONSERVICE']._serialized_end=2803
# @@protoc_insertion_point(module_scope)
