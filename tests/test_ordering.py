from __future__ import annotations

from openapi_diff_checker.checker import compare


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

    def test_genuinely_different_oneof_is_not_equivalent(self, tmp_specs):
        # Order-independence must not mask a real change: dest replaces one of
        # the oneOf subschemas (boolean instead of string).
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
                              - type: number
                              - type: boolean
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "replacing a oneOf subschema is a functional difference"
        )

    def test_genuinely_different_anyof_is_not_equivalent(self, tmp_specs):
        # Order-independence must not mask a real change: dest replaces one of
        # the anyOf subschemas (boolean instead of string).
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
                              - type: number
                              - type: boolean
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "replacing an anyOf subschema is a functional difference"
        )

    def test_genuinely_different_allof_is_not_equivalent(self, tmp_specs):
        # Order-independence must not mask a real change: dest changes a
        # property type inside one of the allOf subschemas.
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
                                  age:
                                    type: integer
                              - type: object
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
                                    type: string
                              - type: object
                                properties:
                                  name:
                                    type: string
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "changing a property type inside an allOf subschema is a "
            "functional difference"
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
