from __future__ import annotations

from openapi_diff_checker.checker import compare


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
