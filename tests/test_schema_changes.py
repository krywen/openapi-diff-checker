from __future__ import annotations

from openapi_diff_checker.checker import compare


def _spec(schema_block: str) -> str:
    return f"""\
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
{schema_block}
    """


class TestSchemaConstraints:
    """Guard: validation constraints are part of the contract and any change
    must be flagged. These are handled by the generic comparison; the tests
    lock that in so a constraint can't silently become cosmetic."""

    def test_maximum_change_is_flagged(self, tmp_specs):
        src = _spec("                        type: integer\n                        maximum: 100")
        dest = _spec("                        type: integer\n                        maximum: 50")
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
        assert any(d.path.endswith("/maximum") for d in result.differences)

    def test_min_length_change_is_flagged(self, tmp_specs):
        src = _spec("                        type: string\n                        minLength: 1")
        dest = _spec("                        type: string\n                        minLength: 3")
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
        assert any(d.path.endswith("/minLength") for d in result.differences)

    def test_pattern_change_is_flagged(self, tmp_specs):
        src = _spec('                        type: string\n                        pattern: "^[a-z]+$"')
        dest = _spec('                        type: string\n                        pattern: "^[A-Z]+$"')
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
        assert any(d.path.endswith("/pattern") for d in result.differences)

    def test_added_constraint_is_flagged(self, tmp_specs):
        # Adding a constraint where there was none narrows the contract.
        src = _spec("                        type: array\n                        items:\n                          type: string")
        dest = _spec(
            "                        type: array\n"
            "                        maxItems: 10\n"
            "                        items:\n"
            "                          type: string"
        )
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
        assert any(d.path.endswith("/maxItems") for d in result.differences)


class TestRequiredProperty:
    """Guard: a schema's `required` array is a set; adding or removing a
    required property name is a functional difference."""

    def test_required_property_added(self, tmp_specs):
        src = _spec(
            "                        type: object\n"
            "                        properties:\n"
            "                          name:\n"
            "                            type: string\n"
            "                          email:\n"
            "                            type: string"
        )
        dest = _spec(
            "                        type: object\n"
            "                        required:\n"
            "                          - email\n"
            "                        properties:\n"
            "                          name:\n"
            "                            type: string\n"
            "                          email:\n"
            "                            type: string"
        )
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False

    def test_required_property_removed_from_list(self, tmp_specs):
        src = _spec(
            "                        type: object\n"
            "                        required:\n"
            "                          - name\n"
            "                          - email\n"
            "                        properties:\n"
            "                          name:\n"
            "                            type: string\n"
            "                          email:\n"
            "                            type: string"
        )
        dest = _spec(
            "                        type: object\n"
            "                        required:\n"
            "                          - name\n"
            "                        properties:\n"
            "                          name:\n"
            "                            type: string\n"
            "                          email:\n"
            "                            type: string"
        )
        src, dest = tmp_specs(src, dest)
        result = compare(src, dest)
        assert result.equivalent is False
        assert any(d.kind == "removed" and "email" in d.detail for d in result.differences)
