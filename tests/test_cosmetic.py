from __future__ import annotations

from openapi_diff_checker.checker import compare


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

    def test_missing_example_is_ignored(self, tmp_specs):
        # An example present on one side but absent on the other is just
        # documentation completeness, not a contract change.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /x:
                post:
                  requestBody:
                    content:
                      application/json:
                        schema:
                          type: object
                          properties:
                            presetFiatAmount:
                              type: number
                              description: The preset fiat amount
                  responses:
                    "200":
                      description: ok
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /x:
                post:
                  requestBody:
                    content:
                      application/json:
                        schema:
                          type: object
                          properties:
                            presetFiatAmount:
                              type: number
                              description: USD amount to deposit
                              example: 50
                  responses:
                    "200":
                      description: ok
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"a missing example should be ignored: {result.differences}"
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
