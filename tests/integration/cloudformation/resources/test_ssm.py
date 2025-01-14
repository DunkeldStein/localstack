import os.path

import pytest

from localstack.utils.common import short_uid


def test_parameter_defaults(deploy_cfn_template, aws_client):
    ssm_parameter_value = f"custom-{short_uid()}"

    stack = deploy_cfn_template(
        template_path=os.path.join(
            os.path.dirname(__file__), "../../templates/ssm_parameter_defaultname.yaml"
        ),
        parameters={"Input": ssm_parameter_value},
    )

    parameter_name = stack.outputs["CustomParameterOutput"]
    assert "CustomParameter" in parameter_name
    param = aws_client.ssm.get_parameter(Name=parameter_name)
    assert param["Parameter"]["Value"] == ssm_parameter_value

    # make sure parameter is deleted
    stack.destroy()

    with pytest.raises(Exception) as ctx:
        aws_client.ssm.get_parameter(Name=parameter_name)
    ctx.match("ParameterNotFound")


@pytest.mark.aws_validated
def test_update_ssm_parameters(deploy_cfn_template, aws_client):
    ssm_parameter_value = f"custom-{short_uid()}"

    stack = deploy_cfn_template(
        template_path=os.path.join(
            os.path.dirname(__file__), "../../templates/ssm_parameter_defaultname.yaml"
        ),
        parameters={"Input": ssm_parameter_value},
    )

    ssm_parameter_value = f"new-custom-{short_uid()}"
    deploy_cfn_template(
        is_update=True,
        stack_name=stack.stack_name,
        template_path=os.path.join(
            os.path.dirname(__file__), "../../templates/ssm_parameter_defaultname.yaml"
        ),
        parameters={"Input": ssm_parameter_value},
    )

    parameter_name = stack.outputs["CustomParameterOutput"]
    param = aws_client.ssm.get_parameter(Name=parameter_name)
    assert param["Parameter"]["Value"] == ssm_parameter_value


@pytest.mark.aws_validated
def test_update_ssm_parameter_tag(deploy_cfn_template, aws_client):
    ssm_parameter_value = f"custom-{short_uid()}"
    tag_value = f"tag-{short_uid()}"

    stack = deploy_cfn_template(
        template_path=os.path.join(
            os.path.dirname(__file__), "../../templates/ssm_parameter_defaultname_withtags.yaml"
        ),
        parameters={
            "Input": ssm_parameter_value,
            "TagValue": tag_value,
        },
    )
    parameter_name = stack.outputs["CustomParameterOutput"]
    ssm_tags = aws_client.ssm.list_tags_for_resource(
        ResourceType="Parameter", ResourceId=parameter_name
    )["TagList"]
    tags_pre_update = {tag["Key"]: tag["Value"] for tag in ssm_tags}
    assert tags_pre_update["A"] == tag_value

    tag_value_new = f"tag-{short_uid()}"
    deploy_cfn_template(
        is_update=True,
        stack_name=stack.stack_name,
        template_path=os.path.join(
            os.path.dirname(__file__), "../../templates/ssm_parameter_defaultname_withtags.yaml"
        ),
        parameters={
            "Input": ssm_parameter_value,
            "TagValue": tag_value_new,
        },
    )

    ssm_tags = aws_client.ssm.list_tags_for_resource(
        ResourceType="Parameter", ResourceId=parameter_name
    )["TagList"]
    tags_post_update = {tag["Key"]: tag["Value"] for tag in ssm_tags}
    assert tags_post_update["A"] == tag_value_new

    # TODO: re-enable after fixing updates in general
    # deploy_cfn_template(
    #     is_update=True,
    #     stack_name=stack.stack_name,
    #     template_path=os.path.join(
    #         os.path.dirname(__file__), "../../templates/ssm_parameter_defaultname.yaml"
    #     ),
    #     parameters={
    #         "Input": ssm_parameter_value,
    #     },
    # )
    #
    # ssm_tags = aws_client.ssm.list_tags_for_resource(ResourceType="Parameter", ResourceId=parameter_name)['TagList']
    # assert ssm_tags == []
