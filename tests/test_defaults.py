from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from openapi_diff_checker.checker import compare


@pytest.fixture
def tmp_specs(tmp_path):
    def _write(src_yaml: str, dest_yaml: str) -> tuple[Path, Path]:
        src = tmp_path / "src.yaml"
        dest = tmp_path / "dest.yaml"
        src.write_text(textwrap.dedent(src_yaml))
        dest.write_text(textwrap.dedent(dest_yaml))
        return src, dest
    return _write


class TestRequiredDefault:
    def test_required_false_vs_omitted_on_parameter(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  parameters:
                    - name: filter
                      in: query
                      required: false
                      schema:
                        type: string
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
                  parameters:
                    - name: filter
                      in: query
                      schema:
                        type: string
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: string
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"required: false vs omitted should be equivalent: {result.differences}"
        )

    def test_required_false_vs_omitted_on_request_body(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                post:
                  requestBody:
                    required: false
                    content:
                      application/json:
                        schema:
                          type: object
                  responses:
                    "201":
                      content:
                        application/json:
                          schema:
                            type: object
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                post:
                  requestBody:
                    content:
                      application/json:
                        schema:
                          type: object
                  responses:
                    "201":
                      content:
                        application/json:
                          schema:
                            type: object
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"required: false vs omitted should be equivalent: {result.differences}"
        )

    def test_required_true_vs_omitted_is_not_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  parameters:
                    - name: id
                      in: query
                      required: true
                      schema:
                        type: string
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
                  parameters:
                    - name: id
                      in: query
                      schema:
                        type: string
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


class TestNullableDefault:
    def test_nullable_false_vs_omitted(self, tmp_specs):
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
                            nullable: false
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
        assert result.equivalent is True, (
            f"nullable: false vs omitted should be equivalent: {result.differences}"
        )

    def test_nullable_true_vs_omitted_is_not_equivalent(self, tmp_specs):
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
                            nullable: true
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


class TestDeprecatedDefault:
    def test_deprecated_false_vs_omitted(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  deprecated: false
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
        assert result.equivalent is True, (
            f"deprecated: false vs omitted should be equivalent: {result.differences}"
        )


class TestAllowEmptyValueDefault:
    def test_allow_empty_value_false_vs_omitted(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  parameters:
                    - name: q
                      in: query
                      allowEmptyValue: false
                      schema:
                        type: string
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
                  parameters:
                    - name: q
                      in: query
                      schema:
                        type: string
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: string
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"allowEmptyValue: false vs omitted should be equivalent: {result.differences}"
        )


class TestAllowReservedDefault:
    def test_allow_reserved_false_vs_omitted(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  parameters:
                    - name: q
                      in: query
                      allowReserved: false
                      schema:
                        type: string
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
                  parameters:
                    - name: q
                      in: query
                      schema:
                        type: string
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: string
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"allowReserved: false vs omitted should be equivalent: {result.differences}"
        )


class TestReadOnlyDefault:
    def test_read_only_false_vs_omitted(self, tmp_specs):
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
                            type: object
                            properties:
                              id:
                                type: integer
                                readOnly: false
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
                            type: object
                            properties:
                              id:
                                type: integer
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"readOnly: false vs omitted should be equivalent: {result.differences}"
        )


class TestWriteOnlyDefault:
    def test_write_only_false_vs_omitted(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                post:
                  requestBody:
                    content:
                      application/json:
                        schema:
                          type: object
                          properties:
                            password:
                              type: string
                              writeOnly: false
                  responses:
                    "201":
                      content:
                        application/json:
                          schema:
                            type: object
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                post:
                  requestBody:
                    content:
                      application/json:
                        schema:
                          type: object
                          properties:
                            password:
                              type: string
                  responses:
                    "201":
                      content:
                        application/json:
                          schema:
                            type: object
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"writeOnly: false vs omitted should be equivalent: {result.differences}"
        )


class TestExclusiveMinimumDefault:
    def test_exclusive_minimum_false_vs_omitted(self, tmp_specs):
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
                            type: integer
                            minimum: 0
                            exclusiveMinimum: false
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
                            minimum: 0
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"exclusiveMinimum: false vs omitted should be equivalent: {result.differences}"
        )


class TestExclusiveMaximumDefault:
    def test_exclusive_maximum_false_vs_omitted(self, tmp_specs):
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
                            type: integer
                            maximum: 100
                            exclusiveMaximum: false
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
                            maximum: 100
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"exclusiveMaximum: false vs omitted should be equivalent: {result.differences}"
        )


class TestAdditionalPropertiesDefault:
    def test_additional_properties_true_vs_omitted(self, tmp_specs):
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
                            type: object
                            additionalProperties: true
                            properties:
                              name:
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
                            type: object
                            properties:
                              name:
                                type: string
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"additionalProperties: true vs omitted should be equivalent: {result.differences}"
        )

    def test_additional_properties_false_vs_omitted_is_not_equivalent(self, tmp_specs):
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
                            type: object
                            additionalProperties: false
                            properties:
                              name:
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
                            type: object
                            properties:
                              name:
                                type: string
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
