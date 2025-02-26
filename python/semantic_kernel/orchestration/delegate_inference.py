# Copyright (c) Microsoft. All rights reserved.

from inspect import Signature, isasyncgenfunction, iscoroutinefunction, signature
from typing import NoReturn

from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.orchestration.delegate_types import DelegateTypes


def _infers(delegate_type):
    def decorator(function):
        function._delegate_type = delegate_type
        return function

    return decorator


def _is_annotation_of_type(annotation, type_to_match) -> bool:
    return (annotation is type_to_match) or (
        # Handle cases where the annotation is provided as a string to avoid circular imports
        # for example: `async def read_async(self, context: "KernelContext"):` in file_io_plugin.py
        isinstance(annotation, str)
        and annotation == type_to_match.__name__
    )


def _has_no_params(signature: Signature) -> bool:
    return len(signature.parameters) == 0


def _return_is_str(signature: Signature) -> bool:
    return signature.return_annotation is str


def _return_is_context(signature: Signature) -> bool:
    from semantic_kernel.orchestration.kernel_context import KernelContext

    return _is_annotation_of_type(signature.return_annotation, KernelContext)


def _return_is_none(signature: Signature) -> bool:
    return signature.return_annotation is None


def _no_return(signature: Signature) -> bool:
    return signature.return_annotation is Signature.empty


def _has_first_param_with_type(signature: Signature, annotation, only: bool = True) -> bool:
    if len(signature.parameters) < 1:
        return False
    if only and len(signature.parameters) != 1:
        return False

    first_param = list(signature.parameters.values())[0]
    return _is_annotation_of_type(first_param.annotation, annotation)


def _has_two_params_second_is_context(signature: Signature) -> bool:
    from semantic_kernel.orchestration.kernel_context import KernelContext

    if len(signature.parameters) < 2:
        return False
    second_param = list(signature.parameters.values())[1]
    return _is_annotation_of_type(second_param.annotation, KernelContext)


def _first_param_is_str(signature: Signature, only: bool = True) -> bool:
    return _has_first_param_with_type(signature, str, only)


def _first_param_is_context(signature: Signature) -> bool:
    from semantic_kernel.orchestration.kernel_context import KernelContext

    return _has_first_param_with_type(signature, KernelContext)


class DelegateInference(KernelBaseModel):
    @staticmethod
    @_infers(DelegateTypes.Void)
    def infer_void(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _has_no_params(signature)
        matches = matches and _return_is_none(signature)
        matches = matches and not awaitable and not is_asyncgenfunc
        return matches

    @staticmethod
    @_infers(DelegateTypes.OutString)
    def infer_out_string(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _has_no_params(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and not awaitable and not is_asyncgenfunc
        return matches

    @staticmethod
    @_infers(DelegateTypes.OutTaskString)
    def infer_out_task_string(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _has_no_params(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InKernelContext)
    def infer_in_kernel_context(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_context(signature)
        matches = matches and _return_is_none(signature)
        matches = matches and not awaitable and not is_asyncgenfunc
        return matches

    @staticmethod
    @_infers(DelegateTypes.InKernelContextOutString)
    def infer_in_kernel_context_out_string(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_context(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and not awaitable and not is_asyncgenfunc
        return matches

    @staticmethod
    @_infers(DelegateTypes.InKernelContextOutTaskString)
    def infer_in_kernel_context_out_task_string(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_context(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.ContextSwitchInKernelContextOutTaskKernelContext)
    def infer_context_switch_in_kernel_context_out_task_kernel_context(
        signature: Signature, awaitable: bool, is_asyncgenfunc: bool
    ) -> bool:
        matches = _first_param_is_context(signature)
        matches = matches and _return_is_context(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InString)
    def infer_in_string(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_str(signature)
        matches = matches and _return_is_none(signature)
        matches = matches and not awaitable and not is_asyncgenfunc
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringOutString)
    def infer_in_string_out_string(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_str(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and not awaitable and not is_asyncgenfunc
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringOutTaskString)
    def infer_in_string_out_task_string(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_str(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringAndContext)
    def infer_in_string_and_context(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_str(signature, only=False)
        matches = matches and _has_two_params_second_is_context(signature)
        matches = matches and _return_is_none(signature)
        matches = matches and not awaitable and not is_asyncgenfunc
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringAndContextOutString)
    def infer_in_string_and_context_out_string(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_str(signature, only=False)
        matches = matches and _has_two_params_second_is_context(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and not awaitable and not is_asyncgenfunc
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringAndContextOutTaskString)
    def infer_in_string_and_context_out_task_string(
        signature: Signature, awaitable: bool, is_asyncgenfunc: bool
    ) -> bool:
        matches = _first_param_is_str(signature, only=False)
        matches = matches and _has_two_params_second_is_context(signature)
        matches = matches and _return_is_str(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.ContextSwitchInStringAndContextOutTaskContext)
    def infer_context_switch_in_string_and_context_out_task_context(
        signature: Signature, awaitable: bool, is_asyncgenfunc: bool
    ) -> bool:
        matches = _first_param_is_str(signature, only=False)
        matches = matches and _has_two_params_second_is_context(signature)
        matches = matches and _return_is_context(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringOutTask)
    def infer_in_string_out_task(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_str(signature)
        matches = matches and _return_is_none(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InContextOutTask)
    def infer_in_context_out_task(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_context(signature)
        matches = matches and _return_is_none(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringAndContextOutTask)
    def infer_in_string_and_context_out_task(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_str(signature, only=False)
        matches = matches and _has_two_params_second_is_context(signature)
        matches = matches and _return_is_none(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.OutTask)
    def infer_out_task(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _has_no_params(signature)
        matches = matches and awaitable
        return matches

    @staticmethod
    @_infers(DelegateTypes.OutAsyncGenerator)
    def infer_out_async_generator(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _has_no_params(signature)
        matches = matches and is_asyncgenfunc
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringOutAsyncGenerator)
    def infer_in_string_out_async_generator(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_str(signature)
        matches = matches and is_asyncgenfunc
        return matches

    @staticmethod
    @_infers(DelegateTypes.InContextOutAsyncGenerator)
    def infer_in_context_out_async_generator(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> bool:
        matches = _first_param_is_context(signature)
        matches = matches and is_asyncgenfunc
        return matches

    @staticmethod
    @_infers(DelegateTypes.InStringAndContextOutAsyncGenerator)
    def infer_in_string_and_context_out_async_generator(
        signature: Signature, awaitable: bool, is_asyncgenfunc: bool
    ) -> bool:
        matches = _first_param_is_str(signature, only=False)
        matches = matches and _has_two_params_second_is_context(signature)
        matches = matches and is_asyncgenfunc
        return matches

    @staticmethod
    @_infers(DelegateTypes.Unknown)
    def infer_unknown(signature: Signature, awaitable: bool, is_asyncgenfunc: bool) -> NoReturn:
        raise KernelException(
            KernelException.ErrorCodes.FunctionTypeNotSupported,
            "Invalid function type detected, unable to infer DelegateType." + f" Function: {signature}",
        )

    @staticmethod
    def infer_delegate_type(function) -> DelegateTypes:
        # Get the function signature
        function_signature = signature(function)

        if _no_return(function_signature):
            raise KernelException(
                KernelException.ErrorCodes.FunctionTypeNotSupported,
                "No return type specified, unable to infer DelegateType.",
            )

        awaitable = iscoroutinefunction(function)
        is_asyncgenfunc = isasyncgenfunction(function)

        for name, value in DelegateInference.__dict__.items():
            wrapped = getattr(value, "__wrapped__", getattr(value, "__func__", None))

            if name.startswith("infer_") and hasattr(wrapped, "_delegate_type"):
                # Get the delegate type
                if wrapped(function_signature, awaitable, is_asyncgenfunc):
                    return wrapped._delegate_type

        return DelegateTypes.Unknown
