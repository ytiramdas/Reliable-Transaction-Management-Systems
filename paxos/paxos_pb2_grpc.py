# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import paxos_pb2 as paxos__pb2

GRPC_GENERATED_VERSION = '1.66.2'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in paxos_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class PaxosStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SetActiveStatus = channel.unary_unary(
                '/Paxos/SetActiveStatus',
                request_serializer=paxos__pb2.SetActiveStatusRequest.SerializeToString,
                response_deserializer=paxos__pb2.SetActiveStatusResponse.FromString,
                _registered_method=True)
        self.HandleTransaction = channel.unary_unary(
                '/Paxos/HandleTransaction',
                request_serializer=paxos__pb2.Transaction.SerializeToString,
                response_deserializer=paxos__pb2.CommitResponse.FromString,
                _registered_method=True)
        self.Prepare = channel.unary_unary(
                '/Paxos/Prepare',
                request_serializer=paxos__pb2.PrepareRequest.SerializeToString,
                response_deserializer=paxos__pb2.PromiseResponse.FromString,
                _registered_method=True)
        self.Accept = channel.unary_unary(
                '/Paxos/Accept',
                request_serializer=paxos__pb2.AcceptRequest.SerializeToString,
                response_deserializer=paxos__pb2.AcceptedResponse.FromString,
                _registered_method=True)
        self.Commit = channel.unary_unary(
                '/Paxos/Commit',
                request_serializer=paxos__pb2.CommitRequest.SerializeToString,
                response_deserializer=paxos__pb2.CommitResponse.FromString,
                _registered_method=True)
        self.PrintBalance = channel.unary_unary(
                '/Paxos/PrintBalance',
                request_serializer=paxos__pb2.PrintBalanceRequest.SerializeToString,
                response_deserializer=paxos__pb2.PrintResponse.FromString,
                _registered_method=True)
        self.PrintLog = channel.unary_unary(
                '/Paxos/PrintLog',
                request_serializer=paxos__pb2.PrintLogRequest.SerializeToString,
                response_deserializer=paxos__pb2.PrintResponse.FromString,
                _registered_method=True)
        self.PrintDB = channel.unary_unary(
                '/Paxos/PrintDB',
                request_serializer=paxos__pb2.PrintDBRequest.SerializeToString,
                response_deserializer=paxos__pb2.PrintResponse.FromString,
                _registered_method=True)
        self.Synchronize = channel.unary_unary(
                '/Paxos/Synchronize',
                request_serializer=paxos__pb2.SynchronizeRequest.SerializeToString,
                response_deserializer=paxos__pb2.SynchronizeResponse.FromString,
                _registered_method=True)
        self.Performance = channel.unary_unary(
                '/Paxos/Performance',
                request_serializer=paxos__pb2.PerformanceRequest.SerializeToString,
                response_deserializer=paxos__pb2.PerformanceResponse.FromString,
                _registered_method=True)
        self.GetCurrentBalance = channel.unary_unary(
                '/Paxos/GetCurrentBalance',
                request_serializer=paxos__pb2.GetCurrentBalanceRequest.SerializeToString,
                response_deserializer=paxos__pb2.GetCurrentBalanceResponse.FromString,
                _registered_method=True)


class PaxosServicer(object):
    """Missing associated documentation comment in .proto file."""

    def SetActiveStatus(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def HandleTransaction(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Prepare(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Accept(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Commit(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PrintBalance(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PrintLog(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PrintDB(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Synchronize(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Performance(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetCurrentBalance(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_PaxosServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'SetActiveStatus': grpc.unary_unary_rpc_method_handler(
                    servicer.SetActiveStatus,
                    request_deserializer=paxos__pb2.SetActiveStatusRequest.FromString,
                    response_serializer=paxos__pb2.SetActiveStatusResponse.SerializeToString,
            ),
            'HandleTransaction': grpc.unary_unary_rpc_method_handler(
                    servicer.HandleTransaction,
                    request_deserializer=paxos__pb2.Transaction.FromString,
                    response_serializer=paxos__pb2.CommitResponse.SerializeToString,
            ),
            'Prepare': grpc.unary_unary_rpc_method_handler(
                    servicer.Prepare,
                    request_deserializer=paxos__pb2.PrepareRequest.FromString,
                    response_serializer=paxos__pb2.PromiseResponse.SerializeToString,
            ),
            'Accept': grpc.unary_unary_rpc_method_handler(
                    servicer.Accept,
                    request_deserializer=paxos__pb2.AcceptRequest.FromString,
                    response_serializer=paxos__pb2.AcceptedResponse.SerializeToString,
            ),
            'Commit': grpc.unary_unary_rpc_method_handler(
                    servicer.Commit,
                    request_deserializer=paxos__pb2.CommitRequest.FromString,
                    response_serializer=paxos__pb2.CommitResponse.SerializeToString,
            ),
            'PrintBalance': grpc.unary_unary_rpc_method_handler(
                    servicer.PrintBalance,
                    request_deserializer=paxos__pb2.PrintBalanceRequest.FromString,
                    response_serializer=paxos__pb2.PrintResponse.SerializeToString,
            ),
            'PrintLog': grpc.unary_unary_rpc_method_handler(
                    servicer.PrintLog,
                    request_deserializer=paxos__pb2.PrintLogRequest.FromString,
                    response_serializer=paxos__pb2.PrintResponse.SerializeToString,
            ),
            'PrintDB': grpc.unary_unary_rpc_method_handler(
                    servicer.PrintDB,
                    request_deserializer=paxos__pb2.PrintDBRequest.FromString,
                    response_serializer=paxos__pb2.PrintResponse.SerializeToString,
            ),
            'Synchronize': grpc.unary_unary_rpc_method_handler(
                    servicer.Synchronize,
                    request_deserializer=paxos__pb2.SynchronizeRequest.FromString,
                    response_serializer=paxos__pb2.SynchronizeResponse.SerializeToString,
            ),
            'Performance': grpc.unary_unary_rpc_method_handler(
                    servicer.Performance,
                    request_deserializer=paxos__pb2.PerformanceRequest.FromString,
                    response_serializer=paxos__pb2.PerformanceResponse.SerializeToString,
            ),
            'GetCurrentBalance': grpc.unary_unary_rpc_method_handler(
                    servicer.GetCurrentBalance,
                    request_deserializer=paxos__pb2.GetCurrentBalanceRequest.FromString,
                    response_serializer=paxos__pb2.GetCurrentBalanceResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Paxos', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('Paxos', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class Paxos(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def SetActiveStatus(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/Paxos/SetActiveStatus',
            paxos__pb2.SetActiveStatusRequest.SerializeToString,
            paxos__pb2.SetActiveStatusResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def HandleTransaction(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/Paxos/HandleTransaction',
            paxos__pb2.Transaction.SerializeToString,
            paxos__pb2.CommitResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Prepare(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/Paxos/Prepare',
            paxos__pb2.PrepareRequest.SerializeToString,
            paxos__pb2.PromiseResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Accept(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/Paxos/Accept',
            paxos__pb2.AcceptRequest.SerializeToString,
            paxos__pb2.AcceptedResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Commit(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/Paxos/Commit',
            paxos__pb2.CommitRequest.SerializeToString,
            paxos__pb2.CommitResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def PrintBalance(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/Paxos/PrintBalance',
            paxos__pb2.PrintBalanceRequest.SerializeToString,
            paxos__pb2.PrintResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def PrintLog(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/Paxos/PrintLog',
            paxos__pb2.PrintLogRequest.SerializeToString,
            paxos__pb2.PrintResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def PrintDB(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/Paxos/PrintDB',
            paxos__pb2.PrintDBRequest.SerializeToString,
            paxos__pb2.PrintResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Synchronize(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/Paxos/Synchronize',
            paxos__pb2.SynchronizeRequest.SerializeToString,
            paxos__pb2.SynchronizeResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Performance(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/Paxos/Performance',
            paxos__pb2.PerformanceRequest.SerializeToString,
            paxos__pb2.PerformanceResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetCurrentBalance(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/Paxos/GetCurrentBalance',
            paxos__pb2.GetCurrentBalanceRequest.SerializeToString,
            paxos__pb2.GetCurrentBalanceResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
