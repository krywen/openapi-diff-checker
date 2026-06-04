from __future__ import annotations

from openapi_diff_checker.checker import compare


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

    def test_explicit_public_equals_implicit_public(self, tmp_specs):
        # src has a global default but the operation opts out with `security: []`
        # (explicitly public). dest has no global and no operation security
        # (implicitly public). Both are public -> equivalent.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            security:
              - bearerAuth: []
            paths:
              /tokenPrice:
                get:
                  security: []
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
              /tokenPrice:
                get:
                  responses:
                    "200":
                      description: ok
        """
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is True, (
            f"explicit `security: []` and implicit public should be "
            f"equivalent: {result.differences}"
        )

    def test_explicit_public_vs_required_is_caught(self, tmp_specs):
        # An explicitly public operation is NOT equivalent to one that requires
        # auth.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /tokenPrice:
                get:
                  security: []
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
              /tokenPrice:
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
        assert result.equivalent is False, (
            "explicit public vs required auth is a functional difference"
        )
