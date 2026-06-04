from __future__ import annotations

from openapi_diff_checker.checker import compare


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

    def test_renamed_path_param_with_real_body_change_is_caught(self, tmp_specs):
        # The path param is merely renamed, but the response type genuinely
        # changes (number -> string): that difference must still surface.
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
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: string
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "a real body change under a renamed path param must be caught"
        )

    def test_different_url_structure_is_not_equivalent(self, tmp_specs):
        # A renamed param is fine, but an extra path segment is a different
        # endpoint and must be flagged.
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
              /tokenPrice/{id}/history:
                get:
                  parameters:
                    - name: id
                      in: path
                      required: true
                      schema:
                        type: string
                  responses:
                    "200":
                      description: ok
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "different URL structure is a different endpoint"
        )


class TestParameterOrdering:
    """Decision: a parameter is identified by (name, in); the order of the
    `parameters` list carries no meaning, so reordering is equivalent."""

    def test_parameters_in_different_order_are_equivalent(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /search:
                get:
                  parameters:
                    - name: q
                      in: query
                      schema:
                        type: string
                    - name: limit
                      in: query
                      schema:
                        type: integer
                    - name: X-Trace
                      in: header
                      schema:
                        type: string
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
              /search:
                get:
                  parameters:
                    - name: X-Trace
                      in: header
                      schema:
                        type: string
                    - name: limit
                      in: query
                      schema:
                        type: integer
                    - name: q
                      in: query
                      schema:
                        type: string
                  responses:
                    "200":
                      description: ok
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"parameter order should not matter: {result.differences}"
        )

    def test_same_name_different_location_is_distinct(self, tmp_specs):
        # name alone is not the key: a query `id` and a path `id` are different
        # parameters, so swapping a location is a real difference.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /item/{id}:
                get:
                  parameters:
                    - name: id
                      in: path
                      required: true
                      schema:
                        type: string
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
              /item/{id}:
                get:
                  parameters:
                    - name: id
                      in: query
                      schema:
                        type: string
                  responses:
                    "200":
                      description: ok
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "same name in a different location is a different parameter"
        )

    def test_changed_parameter_schema_is_caught(self, tmp_specs):
        # Reordering is fine, but a genuine schema change on a matched
        # parameter must still be reported.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /search:
                get:
                  parameters:
                    - name: q
                      in: query
                      schema:
                        type: string
                    - name: limit
                      in: query
                      schema:
                        type: integer
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
              /search:
                get:
                  parameters:
                    - name: limit
                      in: query
                      schema:
                        type: string
                    - name: q
                      in: query
                      schema:
                        type: string
                  responses:
                    "200":
                      description: ok
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "a schema change on the 'limit' parameter must be caught"
        )

    def test_added_parameter_is_caught(self, tmp_specs):
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /search:
                get:
                  parameters:
                    - name: q
                      in: query
                      schema:
                        type: string
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
              /search:
                get:
                  parameters:
                    - name: q
                      in: query
                      schema:
                        type: string
                    - name: limit
                      in: query
                      schema:
                        type: integer
                  responses:
                    "200":
                      description: ok
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False, (
            "an added parameter is a functional difference"
        )
