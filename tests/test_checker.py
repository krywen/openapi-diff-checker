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


class TestCosmeticDifferences:
    def test_description_ignored(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
              description: Old description
            paths:
              /users:
                get:
                  description: Get all users
                  responses:
                    "200":
                      description: Success
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
              description: New description
            paths:
              /users:
                get:
                  description: Fetch users list
                  responses:
                    "200":
                      description: OK
                      content:
                        application/json:
                          schema:
                            type: array
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True

    def test_summary_ignored(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                get:
                  summary: Old summary
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
                  summary: New summary
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: string
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True

    def test_extension_fields_ignored(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                x-internal: true
                get:
                  x-codegen-request-body-name: body
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
        assert result.equivalent is True

    def test_info_contact_license_ignored(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
              contact:
                name: Old Contact
              license:
                name: MIT
              termsOfService: https://old.example.com
            paths: {}
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
              contact:
                name: New Contact
              license:
                name: Apache-2.0
              termsOfService: https://new.example.com
            paths: {}
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True


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


class TestRefResolution:
    def test_inline_vs_ref_equivalent(self, tmp_specs):
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
                            $ref: '#/components/schemas/User'
            components:
              schemas:
                User:
                  type: object
                  properties:
                    name:
                      type: string
                    age:
                      type: integer
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
                              age:
                                type: integer
            components:
              schemas:
                User:
                  type: object
                  properties:
                    name:
                      type: string
                    age:
                      type: integer
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True

    def test_ref_with_different_schema(self, tmp_specs):
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
                            $ref: '#/components/schemas/User'
            components:
              schemas:
                User:
                  type: object
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
                            $ref: '#/components/schemas/User'
            components:
              schemas:
                User:
                  type: object
                  properties:
                    name:
                      type: string
                    email:
                      type: string
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False


class TestSetSemantics:
    def test_required_order_irrelevant(self, tmp_specs):
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
                          required:
                            - name
                            - email
                          properties:
                            name:
                              type: string
                            email:
                              type: string
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
                          required:
                            - email
                            - name
                          properties:
                            name:
                              type: string
                            email:
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
        assert result.equivalent is True

    def test_required_field_added(self, tmp_specs):
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
                          required:
                            - name
                          properties:
                            name:
                              type: string
                            email:
                              type: string
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
                          required:
                            - name
                            - email
                          properties:
                            name:
                              type: string
                            email:
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
        assert result.equivalent is False
        assert any(d.kind == "added" and "email" in d.detail for d in result.differences)


class TestExampleFieldIgnored:
    def test_different_example_values_are_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /user-balance/total:
                get:
                  summary: Get total portfolio value
                  description: Returns the total USD value of all token holdings (excluding USDC).
                  responses:
                    "200":
                      description: Total portfolio value in USD
                      content:
                        application/json:
                          schema:
                            type: number
                            example: 142.0
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /user-balance/total:
                get:
                  summary: Get total portfolio value
                  description: Returns the total USD value of all token holdings (excluding USDC).
                  responses:
                    "200":
                      description: Total portfolio value in USD
                      content:
                        application/json:
                          schema:
                            type: number
                            example: 142.57
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"Expected equivalent but got differences: {result.differences}"
        )


    def test_example_type_change_float_to_int_is_not_cosmetic(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /user-balance/total:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: number
                            example: 123.45
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /user-balance/total:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: number
                            example: 123
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "A float-to-int type change in example should be flagged"
        )

    def test_example_type_change_int_to_float_is_not_cosmetic(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /user-balance/total:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: number
                            example: 1
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /user-balance/total:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: number
                            example: 1.0
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "An int-to-float type change in example should be flagged"
        )


class TestPathOrdering:
    def test_paths_in_different_order_are_equivalent(self, tmp_specs):
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
                            items:
                              type: string
              /items:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: array
                            items:
                              type: integer
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /items:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: array
                            items:
                              type: integer
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
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"Path order should not matter but got differences: {result.differences}"
        )


class TestInfoTitleChange:
    def test_title_is_structural(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Old API
              version: "1.0"
            paths: {}
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: New API
              version: "1.0"
            paths: {}
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
