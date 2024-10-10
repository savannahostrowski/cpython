#ifndef Py_INTERNAL_JIT_H
#define Py_INTERNAL_JIT_H

#ifdef __cplusplus
extern "C" {
#endif

#ifndef Py_BUILD_CORE
#  error "this header requires Py_BUILD_CORE define"
#endif

#ifdef _Py_JIT

#if defined(__x86_64__)
    // For x86_64, use preserve_none
    typedef _Py_CODEUNIT *(*jit_func)(_PyInterpreterFrame *, _PyStackRef *, PyThreadState *) __attribute__((preserve_none));
#else
    // For other platforms, use the default calling convention
    typedef _Py_CODEUNIT *(*jit_func)(_PyInterpreterFrame *, _PyStackRef *, PyThreadState *);
#endif

int _PyJIT_Compile(_PyExecutorObject *executor, const _PyUOpInstruction *trace, size_t length);
void _PyJIT_Free(_PyExecutorObject *executor);

#endif  // _Py_JIT

#ifdef __cplusplus
}
#endif

#endif // !Py_INTERNAL_JIT_H