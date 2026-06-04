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


class TestOrphanComponents:
    """Decision: orphan (unreferenced) component definitions do not affect
    functional equivalence.

    A ``$ref`` is inlined before comparison, so a named component and its
    inline equivalent describe the same contract. Any definition left under
    ``/components`` that no surviving ``$ref`` points to is dead weight and is
    ignored when deciding equivalence.
    """

    def test_ref_to_component_equals_inline(self, tmp_specs):
        # src factors the enum out into a named component and references it...
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /trade:
                post:
                  requestBody:
                    content:
                      application/json:
                        schema:
                          type: object
                          properties:
                            tradeType:
                              $ref: "#/components/schemas/TradeType"
                  responses:
                    "200":
                      description: ok
            components:
              schemas:
                TradeType:
                  type: string
                  enum: [BUY, SELL]
        """
        # ...dest inlines the exact same schema, with no components section.
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /trade:
                post:
                  requestBody:
                    content:
                      application/json:
                        schema:
                          type: object
                          properties:
                            tradeType:
                              type: string
                              enum: [BUY, SELL]
                  responses:
                    "200":
                      description: ok
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"a $ref and its inline equivalent should match: "
            f"{result.differences}"
        )

    def test_unreferenced_orphan_component_is_ignored(self, tmp_specs):
        # Both specs describe the identical API; src merely carries an extra
        # component definition that nothing references.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /trade:
                get:
                  responses:
                    "200":
                      description: ok
            components:
              schemas:
                UnusedThing:
                  type: string
                  enum: [A, B, C]
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /trade:
                get:
                  responses:
                    "200":
                      description: ok
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"orphan components should not affect equivalence: "
            f"{result.differences}"
        )

    def test_security_scheme_definition_change_is_caught(self, tmp_specs):
        # A security scheme is referenced by NAME (not $ref) from `security`,
        # so it is not orphan: a change to its definition must be detected.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /x:
                get:
                  security:
                    - bearerAuth: []
                  responses:
                    "200":
                      description: ok
            components:
              securitySchemes:
                bearerAuth:
                  type: http
                  scheme: bearer
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /x:
                get:
                  security:
                    - bearerAuth: []
                  responses:
                    "200":
                      description: ok
            components:
              securitySchemes:
                bearerAuth:
                  type: http
                  scheme: basic
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "changing a referenced security scheme (bearer -> basic) is a "
            "functional difference"
        )
        assert any("scheme" in d.path for d in result.differences), (
            f"expected the scheme change to be reported: {result.differences}"
        )

    def test_security_scheme_referenced_via_global_security_is_kept(self, tmp_specs):
        # The scheme is referenced only through the GLOBAL security default;
        # a definition change must still be caught after inheritance resolution.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            security:
              - bearerAuth: []
            paths:
              /x:
                get:
                  responses:
                    "200":
                      description: ok
            components:
              securitySchemes:
                bearerAuth:
                  type: http
                  scheme: bearer
                  bearerFormat: JWT
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            security:
              - bearerAuth: []
            paths:
              /x:
                get:
                  responses:
                    "200":
                      description: ok
            components:
              securitySchemes:
                bearerAuth:
                  type: http
                  scheme: bearer
                  bearerFormat: opaque
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "a bearerFormat change on a globally-referenced scheme must be "
            "caught"
        )

    def test_unused_security_scheme_is_still_orphan(self, tmp_specs):
        # A security scheme that no `security` requirement names is genuinely
        # orphan and should not affect equivalence.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /x:
                get:
                  responses:
                    "200":
                      description: ok
            components:
              securitySchemes:
                apiKeyAuth:
                  type: apiKey
                  in: header
                  name: X-API-Key
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /x:
                get:
                  responses:
                    "200":
                      description: ok
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"an unreferenced security scheme is still orphan: "
            f"{result.differences}"
        )


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


class TestServers:
    def test_servers_in_different_order_are_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            servers:
              - url: https://api.example.com/v1
              - url: https://staging.example.com/v1
              - url: https://dev.example.com/v1
            paths: {}
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            servers:
              - url: https://dev.example.com/v1
              - url: https://api.example.com/v1
              - url: https://staging.example.com/v1
            paths: {}
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"server order should not matter: {result.differences}"
        )

    def test_servers_with_different_urls_are_not_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            servers:
              - url: https://api.example.com/v1
              - url: https://staging.example.com/v1
            paths: {}
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            servers:
              - url: https://api.example.com/v1
              - url: https://staging.example.com/v2
            paths: {}
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False

    def test_different_server_list_is_not_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            servers:
              - url: https://api.example.com/v1
              - url: https://staging.example.com/v1
            paths: {}
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            servers:
              - url: https://api.example.com/v1
            paths: {}
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
        assert any(d.path == "/servers" for d in result.differences)


class TestYamlListStyles:
    def test_flow_vs_block_required_list_are_equivalent(self, tmp_specs):
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
                          required: [name, email]
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
        assert result.equivalent is True, (
            f"Flow [name, email] vs block list should be equivalent: {result.differences}"
        )


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


class TestPathParameterNames:
    def test_different_path_param_names_and_query_examples_are_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /tokenPrice/{tokenId}:
                get:
                  parameters:
                    - name: tokenId
                      in: path
                      required: true
                      schema:
                        type: string
                    - name: timeRange
                      in: query
                      schema:
                        type: string
                        example: 1D
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: number
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /tokenPrice/{id}:
                get:
                  parameters:
                    - name: id
                      in: path
                      required: true
                      schema:
                        type: string
                    - name: timeRange
                      in: query
                      schema:
                        type: string
                        example: 3D
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: number
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"Path param names and query example values should be irrelevant: "
            f"{result.differences}"
        )


class TestOneOfOrder:
    def test_oneof_different_order_are_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /value:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            oneOf:
                              - type: number
                              - type: string
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /value:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            oneOf:
                              - type: string
                              - type: number
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"oneOf order should not matter: {result.differences}"
        )


    def test_anyof_different_order_are_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /value:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            anyOf:
                              - type: number
                              - type: string
                              - type: boolean
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /value:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            anyOf:
                              - type: boolean
                              - type: number
                              - type: string
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"anyOf order should not matter: {result.differences}"
        )

    def test_allof_different_order_are_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /value:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            allOf:
                              - type: object
                                properties:
                                  name:
                                    type: string
                              - type: object
                                properties:
                                  age:
                                    type: integer
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /value:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            allOf:
                              - type: object
                                properties:
                                  age:
                                    type: integer
                              - type: object
                                properties:
                                  name:
                                    type: string
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"allOf order should not matter: {result.differences}"
        )


class TestEnumDifferences:
    def test_different_enum_values_are_not_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /tokenPrice:
                get:
                  parameters:
                    - name: timeRange
                      in: query
                      schema:
                        type: string
                        enum: [1H, 1D, 1W, 1M, ALL]
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: number
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /tokenPrice:
                get:
                  parameters:
                    - name: timeRange
                      in: query
                      schema:
                        type: string
                        enum: [1H, 1D, 1W, 1M, MAX]
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: number
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False

    def test_same_enum_values_in_different_order_are_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /tokenPrice:
                get:
                  parameters:
                    - name: timeRange
                      in: query
                      schema:
                        type: string
                        enum: [1H, 1D, 1W, 1M, ALL]
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: number
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /tokenPrice:
                get:
                  parameters:
                    - name: timeRange
                      in: query
                      schema:
                        type: string
                        enum: [ALL, 1M, 1H, 1W, 1D]
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: number
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"enum order should not matter: {result.differences}"
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


class TestSchemaNameIrrelevant:
    def test_different_schema_names_same_structure_are_equivalent(self, tmp_specs):
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
                            $ref: '#/components/schemas/UserResponse'
            components:
              schemas:
                UserResponse:
                  type: object
                  properties:
                    age:
                      type: integer
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
                            $ref: '#/components/schemas/Person'
            components:
              schemas:
                Person:
                  type: object
                  properties:
                    name:
                      type: string
                    age:
                      type: integer
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"Schema names should be irrelevant when structure matches: "
            f"{result.differences}"
        )


class TestRequiredDefaults:
    def test_required_false_vs_omitted_are_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                post:
                  parameters:
                    - name: filter
                      in: query
                      required: false
                      schema:
                        type: string
                  requestBody:
                    required: false
                    content:
                      application/json:
                        schema:
                          type: object
                          properties:
                            name:
                              type: string
                            email:
                              type: string
                  responses:
                    "200":
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
                  parameters:
                    - name: filter
                      in: query
                      schema:
                        type: string
                  requestBody:
                    content:
                      application/json:
                        schema:
                          type: object
                          properties:
                            name:
                              type: string
                            email:
                              type: string
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: object
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"required: false vs omitted should be equivalent "
            f"but got differences: {result.differences}"
        )


class TestResponseCodeQuoting:
    def test_unquoted_vs_quoted_response_code_are_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /users:
                post:
                  responses:
                    200:
                      description: User registered successfully
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
                  responses:
                    "200":
                      description: User registered successfully
                      content:
                        application/json:
                          schema:
                            type: object
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"Quoted vs unquoted response codes should be equivalent "
            f"but got differences: {result.differences}"
        )


class TestInfoMetadataCosmetic:
    def test_title_description_version_differences_are_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Old API
              description: The original description.
              version: "1.0"
            paths: {}
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: New API
              description: A completely rewritten description.
              version: "2.0"
            paths: {}
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"info title/description/version should be cosmetic: "
            f"{result.differences}"
        )


class TestSecurityInheritance:
    """Decision: the same *effective* security expressed differently is
    equivalent.

    A global ``security`` requirement is the default for every operation that
    does not declare its own. So declaring it globally vs. repeating it on each
    operation produces the same effective contract and should compare equal.
    An explicit operation-level ``security: []`` is a real override (the
    operation is public) and is honored, not inherited.
    """

    def test_global_vs_operation_security_are_equivalent(self, tmp_specs):
        # src declares bearerAuth globally; the operation inherits it.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            security:
              - bearerAuth: []
            paths:
              /moonpay/sign-url:
                post:
                  responses:
                    "200":
                      description: ok
            components:
              securitySchemes:
                bearerAuth:
                  type: http
                  scheme: bearer
        """
        # dest declares the identical requirement on the operation itself.
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /moonpay/sign-url:
                post:
                  security:
                    - bearerAuth: []
                  responses:
                    "200":
                      description: ok
            components:
              securitySchemes:
                bearerAuth:
                  type: http
                  scheme: bearer
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"global vs operation-level security should be equivalent: "
            f"{result.differences}"
        )

    def test_operation_override_beats_global_default(self, tmp_specs):
        # Both specs end up with the same effective security: the /public
        # operation is explicitly public, /private requires bearerAuth.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            security:
              - bearerAuth: []
            paths:
              /public:
                get:
                  security: []
                  responses:
                    "200":
                      description: ok
              /private:
                get:
                  responses:
                    "200":
                      description: ok
            components:
              securitySchemes:
                bearerAuth:
                  type: http
                  scheme: bearer
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /public:
                get:
                  security: []
                  responses:
                    "200":
                      description: ok
              /private:
                get:
                  security:
                    - bearerAuth: []
                  responses:
                    "200":
                      description: ok
            components:
              securitySchemes:
                bearerAuth:
                  type: http
                  scheme: bearer
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"effective per-operation security should be equivalent: "
            f"{result.differences}"
        )

    def test_genuinely_different_effective_security_is_caught(self, tmp_specs):
        # src requires bearerAuth on the operation; dest makes it public.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            security:
              - bearerAuth: []
            paths:
              /trade:
                get:
                  responses:
                    "200":
                      description: ok
            components:
              securitySchemes:
                bearerAuth:
                  type: http
                  scheme: bearer
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /trade:
                get:
                  responses:
                    "200":
                      description: ok
            components:
              securitySchemes:
                bearerAuth:
                  type: http
                  scheme: bearer
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "dropping a required auth (operation becomes public) is a "
            "functional difference"
        )
