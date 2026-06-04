from __future__ import annotations

from openapi_diff_checker.checker import compare


class TestLineNumbers:
    """Line numbers must point at the real source location or be omitted —
    never a misleading fallback line."""

    def test_line_resolves_through_path_param_normalization(self, tmp_specs):
        # The path parameter is renamed (itemId vs id), but the reported line
        # for a change under that path must still point at the real source
        # line, not a fabricated ancestor.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /items/{itemId}:
                get:
                  parameters:
                    - name: itemId
                      in: path
                      required: true
                      schema:
                        type: string
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: object
                            properties:
                              price:
                                type: number
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /items/{id}:
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
                            type: object
                            properties:
                              price:
                                type: string
        """
        src_path, dest_path = tmp_specs(src, dest)
        result = compare(src_path, dest_path)

        changes = [d for d in result.differences if d.path.endswith("/price/type")]
        assert len(changes) == 1, result.differences
        diff = changes[0]

        # The reported lines must point at the actual `type:` lines, not an
        # unrelated fallback.
        src_lines = src_path.read_text().splitlines()
        dest_lines = dest_path.read_text().splitlines()
        assert diff.src_line is not None and diff.dest_line is not None
        assert "type: number" in src_lines[diff.src_line - 1]
        assert "type: string" in dest_lines[diff.dest_line - 1]

    def test_inlined_ref_resolves_to_component_definition_line(self, tmp_specs):
        # src factors a schema out behind a $ref; the change surfaces at the
        # use site (after inlining), but the reported src line follows the
        # $ref back to the component definition's real source line.
        src = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /widget:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            $ref: "#/components/schemas/Widget"
            components:
              schemas:
                Widget:
                  type: object
                  properties:
                    size:
                      type: number
        """
        dest = """\
            openapi: "3.0.0"
            info:
              title: Test API
              version: "1.0"
            paths:
              /widget:
                get:
                  responses:
                    "200":
                      content:
                        application/json:
                          schema:
                            type: object
                            properties:
                              size:
                                type: string
        """
        src_path, dest_path = tmp_specs(src, dest)
        result = compare(src_path, dest_path)

        changes = [d for d in result.differences if d.path.endswith("/size/type")]
        assert len(changes) == 1, result.differences
        diff = changes[0]
        # src is inlined from a $ref; the line follows the ref back to the
        # Widget component definition's `type: number` line.
        src_lines = src_path.read_text().splitlines()
        assert diff.src_line is not None
        assert "type: number" in src_lines[diff.src_line - 1]
        # dest defines it inline, so its line resolves directly.
        dest_lines = dest_path.read_text().splitlines()
        assert "type: string" in dest_lines[diff.dest_line - 1]

    def test_plain_value_change_reports_both_lines(self, tmp_specs):
        # A change on an ordinary (non-normalized, non-inlined) path resolves
        # to the correct line in both files.
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
        src_path, dest_path = tmp_specs(src, dest)
        result = compare(src_path, dest_path)

        changes = [d for d in result.differences if d.path.endswith("/schema/type")]
        assert len(changes) == 1, result.differences
        diff = changes[0]
        src_lines = src_path.read_text().splitlines()
        dest_lines = dest_path.read_text().splitlines()
        assert "type: string" in src_lines[diff.src_line - 1]
        assert "type: integer" in dest_lines[diff.dest_line - 1]

    def test_added_key_has_line_only_on_the_side_present(self, tmp_specs):
        # A response present only in dest: the dest line points at it, the
        # src line is omitted (the key does not exist in src).
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
                      description: ok
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
                      description: ok
                    "404":
                      description: missing
        """
        src_path, dest_path = tmp_specs(src, dest)
        result = compare(src_path, dest_path)

        added = [d for d in result.differences if d.path.endswith("/responses/404")]
        assert len(added) == 1, result.differences
        diff = added[0]
        # The key is absent in src, so no src line; the dest line points into
        # the added 404 block (its body — a mapping node starts at its first
        # child).
        assert diff.src_line is None
        dest_lines = dest_path.read_text().splitlines()
        assert "description: missing" in dest_lines[diff.dest_line - 1]
