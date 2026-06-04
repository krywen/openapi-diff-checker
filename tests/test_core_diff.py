from __future__ import annotations

from openapi_diff_checker.checker import compare


class TestIdenticalSpecs:
    def test_same_file(self, tmp_specs):
        spec = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: array
                            items:
                              type: string
        """
        src, dest = tmp_specs(spec, spec)
        result = compare(src, dest)
        assert result.equivalent is True
        assert result.differences == []


class TestStructuralDifferences:
    def test_path_added(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: array
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: array
              /items:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: array
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
        assert any(d.kind == "added" and "/items" in d.path for d in result.differences)

    def test_path_removed(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: string
              /items:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: string
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: string
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
        assert any(d.kind == "removed" and "/items" in d.path for d in result.differences)

    def test_schema_type_changed(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: string
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: integer
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
        assert any(d.kind == "changed" and "type" in d.path for d in result.differences)

    def test_response_code_added(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: string
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: string
                    "404":
                      content:
                        application/json:
                          schema:
                            type: object
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
        assert any(d.kind == "added" and "404" in d.path for d in result.differences)

    def test_value_type_changed(self, tmp_specs):
        # The `type` value is a scalar string in one spec and a list in the
        # other (OpenAPI 3.1 nullable syntax). The node's Python type differs
        # (str vs list), so it is reported as a "type_changed" difference.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: string
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type:
                              - string
                              - "null"
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
        assert any(
            d.kind == "type_changed" and d.path.endswith("/type")
            for d in result.differences
        ), f"expected a type_changed on /type, got: {result.differences}"
