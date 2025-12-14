"""Tests for sampling profiler stack filtering functionality."""

import unittest
from types import SimpleNamespace

from profiling.sampling.collector import compile_stack_filter


def make_frame(filename, funcname):
    """Create a mock frame object with filename and funcname attributes."""
    return SimpleNamespace(filename=filename, funcname=funcname)


class TestCompileStackFilter(unittest.TestCase):
    """Test the compile_stack_filter function."""

    # --- No filter (returns None) ---

    def test_no_filter_none(self):
        """Test that None filter returns None matcher."""
        matcher = compile_stack_filter(None)
        self.assertIsNone(matcher)

    def test_no_filter_empty_string(self):
        """Test that empty string filter returns None matcher."""
        matcher = compile_stack_filter("")
        self.assertIsNone(matcher)

    # --- Simple text matching ---

    def test_simple_text_matches_filename(self):
        """Test simple text matches anywhere in filename."""
        matcher = compile_stack_filter("database")
        self.assertTrue(matcher(make_frame("/app/database/models.py", "save")))
        self.assertTrue(matcher(make_frame("/app/database.py", "query")))
        self.assertFalse(matcher(make_frame("/app/views.py", "render")))

    def test_simple_text_matches_funcname(self):
        """Test simple text matches anywhere in function name."""
        matcher = compile_stack_filter("handle_request")
        self.assertTrue(matcher(make_frame("/app/views.py", "handle_request")))
        self.assertTrue(matcher(make_frame("/app/api.py", "do_handle_request_async")))
        self.assertFalse(matcher(make_frame("/app/views.py", "render")))

    def test_simple_text_case_insensitive(self):
        """Test simple text matching is case-insensitive."""
        matcher = compile_stack_filter("DATABASE")
        self.assertTrue(matcher(make_frame("/app/database.py", "query")))
        self.assertTrue(matcher(make_frame("/app/Database.py", "Query")))

        matcher = compile_stack_filter("render")
        self.assertTrue(matcher(make_frame("/app/views.py", "Render")))
        self.assertTrue(matcher(make_frame("/app/views.py", "RENDER")))

    def test_simple_text_partial_match(self):
        """Test simple text matches partial strings."""
        matcher = compile_stack_filter("save")
        self.assertTrue(matcher(make_frame("/app/models.py", "save_user")))
        self.assertTrue(matcher(make_frame("/app/models.py", "do_save")))
        self.assertTrue(matcher(make_frame("/app/models.py", "autosave")))

    # --- File path matching ---

    def test_filepath_matches_end_of_filename(self):
        """Test file path pattern matches end of filename."""
        matcher = compile_stack_filter("services/user_service.py")
        self.assertTrue(matcher(make_frame("/app/services/user_service.py", "get_user")))
        self.assertTrue(matcher(make_frame("/home/dev/myapp/services/user_service.py", "save")))
        self.assertFalse(matcher(make_frame("/app/services/order_service.py", "get_order")))

    def test_filepath_py_suffix_triggers_endswith(self):
        """Test that .py suffix triggers endswith matching."""
        matcher = compile_stack_filter("models.py")
        self.assertTrue(matcher(make_frame("/app/models.py", "save")))
        self.assertTrue(matcher(make_frame("/long/path/to/models.py", "query")))
        self.assertFalse(matcher(make_frame("/app/models_backup.py", "save")))

    def test_filepath_slash_triggers_endswith(self):
        """Test that / in pattern triggers endswith matching."""
        matcher = compile_stack_filter("app/views.py")
        self.assertTrue(matcher(make_frame("/home/user/app/views.py", "func")))
        # Note: "myapp/views.py" ends with "app/views.py", so it matches
        self.assertTrue(matcher(make_frame("/home/user/myapp/views.py", "func")))
        # This won't match because the path structure is different
        self.assertFalse(matcher(make_frame("/home/user/app/other.py", "func")))

    def test_filepath_case_insensitive(self):
        """Test file path matching is case-insensitive."""
        matcher = compile_stack_filter("Services/User_Service.py")
        self.assertTrue(matcher(make_frame("/app/services/user_service.py", "get")))

    # --- Pytest-style patterns (::) ---

    def test_pytest_style_file_and_function(self):
        """Test pytest-style file.py::function pattern."""
        matcher = compile_stack_filter("api.py::get_users")
        self.assertTrue(matcher(make_frame("/app/api.py", "get_users")))
        self.assertTrue(matcher(make_frame("/app/api.py", "get_users_paginated")))
        self.assertFalse(matcher(make_frame("/app/api.py", "delete_users")))
        self.assertFalse(matcher(make_frame("/app/views.py", "get_users")))

    def test_pytest_style_file_and_class(self):
        """Test pytest-style file.py::ClassName pattern."""
        matcher = compile_stack_filter("views.py::UserView")
        # Assuming funcname contains qualified name like "UserView.get"
        self.assertTrue(matcher(make_frame("/app/views.py", "UserView.get")))
        self.assertTrue(matcher(make_frame("/app/views.py", "UserView.post")))
        self.assertFalse(matcher(make_frame("/app/views.py", "OrderView.get")))

    def test_pytest_style_file_class_method(self):
        """Test pytest-style file.py::Class::method pattern."""
        matcher = compile_stack_filter("api.py::UserView::get")
        # Pattern becomes "userview.get" and checks if it's in funcname
        self.assertTrue(matcher(make_frame("/app/api.py", "UserView.get")))
        self.assertFalse(matcher(make_frame("/app/api.py", "UserView.post")))
        self.assertFalse(matcher(make_frame("/app/api.py", "OrderView.get")))
        self.assertFalse(matcher(make_frame("/app/views.py", "UserView.get")))

    def test_pytest_style_case_insensitive(self):
        """Test pytest-style patterns are case-insensitive."""
        matcher = compile_stack_filter("API.py::UserView::GET")
        self.assertTrue(matcher(make_frame("/app/api.py", "userview.get")))

        matcher = compile_stack_filter("api.py::userview::get")
        self.assertTrue(matcher(make_frame("/app/API.py", "UserView.Get")))

    def test_pytest_style_file_endswith(self):
        """Test pytest-style patterns use endswith for file part."""
        matcher = compile_stack_filter("api.py::get")
        self.assertTrue(matcher(make_frame("/long/path/api.py", "get_data")))
        # Note: "myapi.py" ends with "api.py", so the file part matches
        self.assertTrue(matcher(make_frame("/app/myapi.py", "get_data")))
        # This won't match because funcname doesn't contain "get"
        self.assertFalse(matcher(make_frame("/app/api.py", "fetch_data")))

    # --- Edge cases ---

    def test_frame_missing_attributes(self):
        """Test handling frames with missing attributes."""
        matcher = compile_stack_filter("test")
        # Frame without filename attribute
        frame_no_filename = SimpleNamespace(funcname="test_func")
        self.assertTrue(matcher(frame_no_filename))

        # Frame without funcname attribute
        frame_no_funcname = SimpleNamespace(filename="/app/test.py")
        self.assertTrue(matcher(frame_no_funcname))

        # Frame without either attribute
        empty_frame = SimpleNamespace()
        self.assertFalse(matcher(empty_frame))

    def test_frame_with_none_values(self):
        """Test handling frames with None attribute values."""
        matcher = compile_stack_filter("test")
        # Frame with explicit None values (not missing attributes)
        frame_none_filename = SimpleNamespace(filename=None, funcname="test_func")
        self.assertTrue(matcher(frame_none_filename))

        frame_none_funcname = SimpleNamespace(filename="/app/test.py", funcname=None)
        self.assertTrue(matcher(frame_none_funcname))

        frame_both_none = SimpleNamespace(filename=None, funcname=None)
        self.assertFalse(matcher(frame_both_none))

    def test_special_characters_in_pattern(self):
        """Test patterns with special characters."""
        # Dots in pattern (common in filenames)
        matcher = compile_stack_filter("test.utils")
        self.assertTrue(matcher(make_frame("/app/test.utils.py", "func")))

        # Underscores
        matcher = compile_stack_filter("my_module")
        self.assertTrue(matcher(make_frame("/app/my_module.py", "func")))

    def test_empty_filename_or_funcname(self):
        """Test matching against empty filename or funcname."""
        matcher = compile_stack_filter("test")
        self.assertFalse(matcher(make_frame("", "")))
        self.assertTrue(matcher(make_frame("test.py", "")))
        self.assertTrue(matcher(make_frame("", "test_func")))


class TestStackFilterIntegration(unittest.TestCase):
    """Integration tests for stack filtering with collector-like usage."""

    def test_filter_matches_any_frame_in_stack(self):
        """Test that filter can be used to check if any frame matches."""
        matcher = compile_stack_filter("database")

        stack = [
            make_frame("/app/views.py", "handle_request"),
            make_frame("/app/services.py", "get_user"),
            make_frame("/app/database/models.py", "query"),
            make_frame("/usr/lib/python/sqlite3.py", "execute"),
        ]

        # Simulate collector's _stack_matches_filter logic
        matches = any(matcher(frame) for frame in stack)
        self.assertTrue(matches)

    def test_filter_no_match_in_stack(self):
        """Test stack with no matching frames."""
        matcher = compile_stack_filter("redis")

        stack = [
            make_frame("/app/views.py", "handle_request"),
            make_frame("/app/database/models.py", "query"),
        ]

        matches = any(matcher(frame) for frame in stack)
        self.assertFalse(matches)

    def test_filter_with_qualname_methods(self):
        """Test filtering with Python's co_qualname style function names."""
        # Python stores method names as "ClassName.method_name" in co_qualname
        matcher = compile_stack_filter("api.py::UserAPI::fetch")

        stack = [
            make_frame("/app/api.py", "UserAPI.fetch"),
            make_frame("/app/api.py", "UserAPI.validate"),
            make_frame("/app/http.py", "request"),
        ]

        matching_frames = [f for f in stack if matcher(f)]
        self.assertEqual(len(matching_frames), 1)
        self.assertEqual(matching_frames[0].funcname, "UserAPI.fetch")


if __name__ == "__main__":
    unittest.main()
