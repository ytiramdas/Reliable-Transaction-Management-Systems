# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: controller.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'controller.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10\x63ontroller.proto\x12\x04pbft\"F\n\x12TransactionRequest\x12\x0e\n\x06sender\x18\x01 \x01(\t\x12\x10\n\x08receiver\x18\x02 \x01(\t\x12\x0e\n\x06\x61mount\x18\x03 \x01(\x05\"7\n\x13TransactionResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"\x8f\x01\n\x0cReplyMessage\x12\x0c\n\x04view\x18\x01 \x01(\x05\x12\x17\n\x0fsequence_number\x18\x02 \x01(\x05\x12\x11\n\tclient_id\x18\x03 \x01(\x05\x12\x12\n\nreplica_id\x18\x04 \x01(\x05\x12\x0e\n\x06result\x18\x05 \x01(\t\x12\x11\n\tsignature\x18\x06 \x01(\x0c\x12\x0e\n\x06status\x18\x07 \x01(\x08\"1\n\rReplyResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t2\x95\x01\n\x11\x43ontrollerService\x12H\n\x11HandleTransaction\x12\x18.pbft.TransactionRequest\x1a\x19.pbft.TransactionResponse\x12\x36\n\x0bHandleReply\x12\x12.pbft.ReplyMessage\x1a\x13.pbft.ReplyResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'controller_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_TRANSACTIONREQUEST']._serialized_start=26
  _globals['_TRANSACTIONREQUEST']._serialized_end=96
  _globals['_TRANSACTIONRESPONSE']._serialized_start=98
  _globals['_TRANSACTIONRESPONSE']._serialized_end=153
  _globals['_REPLYMESSAGE']._serialized_start=156
  _globals['_REPLYMESSAGE']._serialized_end=299
  _globals['_REPLYRESPONSE']._serialized_start=301
  _globals['_REPLYRESPONSE']._serialized_end=350
  _globals['_CONTROLLERSERVICE']._serialized_start=353
  _globals['_CONTROLLERSERVICE']._serialized_end=502
# @@protoc_insertion_point(module_scope)
