from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
import fennec_api.sdmx_v21.parser.models as models

config = ParserConfig()
context = XmlContext()
parser = XmlParser(config=config, context=context)


def parse_structure(content: bytes) -> models.Structure | models.Error:
    return parser.from_bytes(content)


def parse_data(
    content: bytes,
) -> models.GenericData | models.StructureSpecificData | models.Error:
    return parser.from_bytes(content)
