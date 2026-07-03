# tests/tools/test_tool_spec_manifest.py

from arvis.tools.spec import ToolSpec


def test_manifest_defaults_describe_a_sovereign_tool() -> None:
    spec = ToolSpec(name="calendar.read", description="Read the calendar.")
    assert spec.provider is None
    assert spec.data_egress is False
    assert spec.data_class == "unspecified"
    assert spec.required_consent is None
    assert spec.reversible is True
    # No provider => stays within the local trust boundary.
    assert spec.crosses_trust_boundary is False


def test_connected_read_tool_crosses_boundary_without_egress() -> None:
    spec = ToolSpec(
        name="legifrance.search",
        description="Search public law.",
        provider="legifrance",
        data_egress=False,
        data_class="public",
        required_consent="legal_sources",
    )
    assert spec.crosses_trust_boundary is True
    assert spec.data_egress is False


def test_connected_egress_tool_is_fully_flagged() -> None:
    spec = ToolSpec(
        name="notion.create_page",
        description="Create a page in Notion.",
        provider="notion",
        data_egress=True,
        data_class="personal",
        required_consent="notion_access",
        reversible=False,
        side_effectful=True,
    )
    assert spec.crosses_trust_boundary is True
    assert spec.data_egress is True
    assert spec.reversible is False


def test_existing_governance_fields_are_unchanged() -> None:
    # The manifest additions default so prior specs behave identically.
    spec = ToolSpec(
        name="read_status",
        description="Read a service status.",
        side_effectful=False,
        max_risk=0.5,
    )
    assert spec.max_risk == 0.5
    assert spec.requires_confirmation is False
    assert spec.audit_required is False
    assert spec.crosses_trust_boundary is False
