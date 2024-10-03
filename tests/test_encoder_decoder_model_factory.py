# Copyright contributors to the Terratorch project

import pytest
import torch

from terratorch.models import EncoderDecoderFactory
from terratorch.models.backbones.prithvi_vit import PRETRAINED_BANDS
from terratorch.models.model import AuxiliaryHead

NUM_CHANNELS = 6
NUM_CLASSES = 2
EXPECTED_SEGMENTATION_OUTPUT_SHAPE = (1, NUM_CLASSES, 224, 224)
EXPECTED_REGRESSION_OUTPUT_SHAPE = (1, 224, 224)
EXPECTED_CLASSIFICATION_OUTPUT_SHAPE = (1, NUM_CLASSES)

PIXELWISE_TASK_EXPECTED_OUTPUT = [
    ("regression", EXPECTED_REGRESSION_OUTPUT_SHAPE),
    ("segmentation", EXPECTED_SEGMENTATION_OUTPUT_SHAPE),
]


@pytest.fixture(scope="session")
def model_factory() -> EncoderDecoderFactory:
    return EncoderDecoderFactory()


@pytest.fixture(scope="session")
def model_input() -> torch.Tensor:
    return torch.ones((1, NUM_CHANNELS, 224, 224))


@pytest.mark.parametrize("backbone", ["prithvi_vit_100", "prithvi_vit_300"])
def test_create_classification_model(backbone, model_factory: EncoderDecoderFactory, model_input):
    model = model_factory.build_model(
        "classification",
        backbone=backbone,
        decoder="IdentityDecoder",
        backbone_bands=PRETRAINED_BANDS,
        backbone_pretrained=False,
        num_classes=NUM_CLASSES,
    )
    model.eval()

    with torch.no_grad():
        assert model(model_input).output.shape == EXPECTED_CLASSIFICATION_OUTPUT_SHAPE


@pytest.mark.parametrize("backbone", ["prithvi_vit_100", "prithvi_vit_300"])
def test_create_classification_model_no_in_channels(backbone, model_factory: EncoderDecoderFactory, model_input):
    model = model_factory.build_model(
        "classification",
        backbone=backbone,
        decoder="IdentityDecoder",
        backbone_bands=PRETRAINED_BANDS,
        backbone_pretrained=False,
        num_classes=NUM_CLASSES,
    )
    model.eval()

    with torch.no_grad():
        assert model(model_input).output.shape == EXPECTED_CLASSIFICATION_OUTPUT_SHAPE


@pytest.mark.parametrize("backbone", ["prithvi_vit_100"])
@pytest.mark.parametrize("task,expected", PIXELWISE_TASK_EXPECTED_OUTPUT)
@pytest.mark.parametrize("decoder", ["FCNDecoder", "UperNetDecoder", "IdentityDecoder"])
def test_create_pixelwise_model(backbone, task, expected, decoder, model_factory: EncoderDecoderFactory, model_input):
    model_args = {
        "task": task,
        "backbone": backbone,
        "decoder": decoder,
        "backbone_bands": PRETRAINED_BANDS,
        "backbone_pretrained": False,
    }

    if task == "segmentation":
        model_args["num_classes"] = NUM_CLASSES
    if decoder == "UperNetDecoder":
        model_args["backbone_out_indices"] = [1, 2, 3, 4]
        model_args["decoder_scale_modules"] = True

    model = model_factory.build_model(**model_args)
    model.eval()

    with torch.no_grad():
        assert model(model_input).output.shape == expected


@pytest.mark.parametrize("backbone", ["prithvi_vit_100"])
@pytest.mark.parametrize("task,expected", PIXELWISE_TASK_EXPECTED_OUTPUT)
@pytest.mark.parametrize("decoder", ["FCNDecoder", "UperNetDecoder", "IdentityDecoder"])
def test_create_pixelwise_model_no_in_channels(
    backbone, task, expected, decoder, model_factory: EncoderDecoderFactory, model_input
):
    model_args = {
        "task": task,
        "backbone": backbone,
        "decoder": decoder,
        "backbone_bands": PRETRAINED_BANDS,
        "backbone_pretrained": False,
    }

    if task == "segmentation":
        model_args["num_classes"] = NUM_CLASSES
    if decoder == "UperNetDecoder":
        model_args["backbone_out_indices"] = [1, 2, 3, 4]
        model_args["decoder_scale_modules"] = True

    model = model_factory.build_model(**model_args)
    model.eval()

    with torch.no_grad():
        assert model(model_input).output.shape == expected


@pytest.mark.parametrize("backbone", ["prithvi_vit_100"])
@pytest.mark.parametrize("task,expected", PIXELWISE_TASK_EXPECTED_OUTPUT)
@pytest.mark.parametrize("decoder", ["FCNDecoder", "UperNetDecoder", "IdentityDecoder"])
def test_create_pixelwise_model_with_aux_heads(
    backbone, task, expected, decoder, model_factory: EncoderDecoderFactory, model_input
):
    aux_heads_name = ["first_aux", "second_aux"]
    model_args = {
        "task": task,
        "backbone": backbone,
        "decoder": decoder,
        "backbone_in_chans": NUM_CHANNELS,
        "backbone_bands": PRETRAINED_BANDS,
        "backbone_pretrained": False,
        "aux_decoders": [AuxiliaryHead(name, "FCNDecoder", None) for name in aux_heads_name],
    }
    if task == "segmentation":
        model_args["num_classes"] = NUM_CLASSES

    if decoder == "UperNetDecoder":
        model_args["backbone_out_indices"] = [1, 2, 3, 4]
        model_args["decoder_scale_modules"] = True

    model = model_factory.build_model(**model_args)
    model.eval()

    with torch.no_grad():
        model_output = model(model_input)
        assert model_output.output.shape == expected

        assert len(model_output.auxiliary_heads.keys() & aux_heads_name) == len(aux_heads_name)
        for _, output in model_output.auxiliary_heads.items():
            assert output.shape == expected


@pytest.mark.parametrize("backbone", ["prithvi_vit_100"])
@pytest.mark.parametrize("task,expected", PIXELWISE_TASK_EXPECTED_OUTPUT)
@pytest.mark.parametrize("decoder", ["FCNDecoder", "UperNetDecoder", "IdentityDecoder"])
def test_create_pixelwise_model_with_extra_bands(
    backbone, task, expected, decoder, model_factory: EncoderDecoderFactory
):
    model_args = {
        "task": task,
        "backbone": backbone,
        "decoder": decoder,
        "backbone_in_chans": NUM_CHANNELS + 1,
        "backbone_bands": [*PRETRAINED_BANDS, 7],
        "backbone_pretrained": False,
    }
    if task == "segmentation":
        model_args["num_classes"] = NUM_CLASSES

    if decoder == "UperNetDecoder":
        model_args["backbone_out_indices"] = [1, 2, 3, 4]
        model_args["decoder_scale_modules"] = True
    model = model_factory.build_model(**model_args)
    model.eval()
    model_input = torch.ones((1, NUM_CHANNELS + 1, 224, 224))
    with torch.no_grad():
        assert model(model_input).output.shape == expected
