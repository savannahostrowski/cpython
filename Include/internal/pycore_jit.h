#ifndef Py_INTERNAL_JIT_H
#define Py_INTERNAL_JIT_H

#ifdef __cplusplus
extern "C" {
#endif

#ifndef Py_BUILD_CORE
#  error "this header requires Py_BUILD_CORE define"
#endif

#ifdef _Py_JIT

    #ifdef __APPLE__
        #include <TargetConditionals.h>
    
        #if TARGET_OS_MAC && defined(__arm64__)
            // clang 19 does not support preserve_none on arm64
            typedef _Py_CODEUNIT *(*jit_func)(_PyInterpreterFrame *, _PyStackRef *, PyThreadState *);
        #else
            // For other platforms, use preserve_none
            typedef _Py_CODEUNIT *(*jit_func)(_PyInterpreterFrame *, _PyStackRef *, PyThreadState *) __attribute__((preserve_none));
        #endif
    #else
        // For other platforms, use preserve_none
        typedef _Py_CODEUNIT *(*jit_func)(_PyInterpreterFrame *, _PyStackRef *, PyThreadState *) __attribute__((preserve_none));
    #endif

int _PyJIT_Compile(_PyExecutorObject *executor, const _PyUOpInstruction *trace, size_t length);
void _PyJIT_Free(_PyExecutorObject *executor);

#endif  // _Py_JIT

#ifdef __cplusplus
}
#endif

#endif // !Py_INTERNAL_JIT_H