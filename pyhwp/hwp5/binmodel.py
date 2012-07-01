# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

from .dataio import (readn, read_struct_attributes,
                     CompoundType,
                     ArrayType,
                     StructType, Struct, Flags, Enum, BYTE, WORD, UINT32,
                     UINT16, INT32, INT16, UINT8, INT8, DOUBLE, ARRAY, N_ARRAY,
                     SHWPUNIT, HWPUNIT16, HWPUNIT, BSTR, WCHAR)
from .tagids import (tagnames, HWPTAG_DOCUMENT_PROPERTIES, HWPTAG_ID_MAPPINGS,
                     HWPTAG_BIN_DATA, HWPTAG_FACE_NAME, HWPTAG_BORDER_FILL,
                     HWPTAG_CHAR_SHAPE, HWPTAG_TAB_DEF, HWPTAG_NUMBERING,
                     HWPTAG_BULLET, HWPTAG_PARA_SHAPE, HWPTAG_STYLE,
                     HWPTAG_DOC_DATA, HWPTAG_DISTRIBUTE_DOC_DATA,
                     HWPTAG_COMPATIBLE_DOCUMENT, HWPTAG_LAYOUT_COMPATIBILITY,
                     HWPTAG_PARA_HEADER, HWPTAG_PARA_TEXT,
                     HWPTAG_PARA_CHAR_SHAPE, HWPTAG_PARA_LINE_SEG,
                     HWPTAG_PARA_RANGE_TAG, HWPTAG_CTRL_HEADER,
                     HWPTAG_LIST_HEADER, HWPTAG_PAGE_DEF,
                     HWPTAG_FOOTNOTE_SHAPE, HWPTAG_PAGE_BORDER_FILL,
                     HWPTAG_SHAPE_COMPONENT, HWPTAG_TABLE,
                     HWPTAG_SHAPE_COMPONENT_LINE,
                     HWPTAG_SHAPE_COMPONENT_RECTANGLE,
                     HWPTAG_SHAPE_COMPONENT_ELLIPSE,
                     HWPTAG_SHAPE_COMPONENT_ARC,
                     HWPTAG_SHAPE_COMPONENT_POLYGON,
                     HWPTAG_SHAPE_COMPONENT_CURVE, HWPTAG_SHAPE_COMPONENT_OLE,
                     HWPTAG_SHAPE_COMPONENT_PICTURE,
                     HWPTAG_SHAPE_COMPONENT_CONTAINER, HWPTAG_CTRL_DATA,
                     HWPTAG_CTRL_EQEDIT, HWPTAG_SHAPE_COMPONENT_TEXTART,
                     HWPTAG_FORBIDDEN_CHAR)
from .importhelper import importStringIO
from . import dataio


StringIO = importStringIO()


def parse_model_attributes(model, attributes, context):
    return read_struct_attributes(model, attributes, context,
                                         context['stream'])


def typed_model_attributes(model, attributes, context):
    def popvalue(member):
        name = member['name']
        if name in attributes:
            return attributes.pop(name)
        else:
            return member['type']()

    if issubclass(model, RecordModel):
        for d in model.iter_members_with_inherited(context, popvalue):
            yield d

    # remnants
    for name, value in attributes.iteritems():
        yield dict(name=name, value=value, type=type(value))

tag_models = dict()


class RecordModelType(StructType):
    def __init__(cls, name, bases, attrs):
        super(RecordModelType, cls).__init__(name, bases, attrs)
        if 'tagid' in attrs:
            tagid = attrs['tagid']
            existing = tag_models.get(tagid)
            assert not tagid in tag_models,\
                    ('duplicated RecordModels for tagid \'%s\': '
                    + 'new=%s, existing=%s'
                    % (tagnames[tagid], name, existing.__name__))
            tag_models[tagid] = cls


class RecordModel(object):
    __metaclass__ = RecordModelType

    def attributes():
        if False:
            yield
    attributes = staticmethod(attributes)


class DocumentProperties(RecordModel):
    tagid = HWPTAG_DOCUMENT_PROPERTIES

    def attributes():
        yield UINT16, 'section_count',
        yield UINT16, 'page_startnum',
        yield UINT16, 'footnote_startnum',
        yield UINT16, 'endnote_startnum',
        yield UINT16, 'picture_startnum',
        yield UINT16, 'table_startnum',
        yield UINT16, 'math_startnum',
        yield UINT32, 'list_id',
        yield UINT32, 'paragraph_id',
        yield UINT32, 'character_unit_loc_in_paragraph',
        #yield UINT32, 'flags',   # DIFFSPEC
    attributes = staticmethod(attributes)


class IdMappings(RecordModel):
    tagid = HWPTAG_ID_MAPPINGS

    def attributes():
        yield UINT16, 'bindata',
        yield UINT16, 'ko_fonts',
        yield UINT16, 'en_fonts',
        yield UINT16, 'cn_fonts',
        yield UINT16, 'jp_fonts',
        yield UINT16, 'other_fonts',
        yield UINT16, 'symbol_fonts',
        yield UINT16, 'user_fonts',
        yield UINT16, 'borderfills',
        yield UINT16, 'charshapes',
        yield UINT16, 'tabdefs',
        yield UINT16, 'numberings',
        yield UINT16, 'bullets',
        yield UINT16, 'parashapes',
        yield UINT16, 'styles',
        yield UINT16, 'memoshapes',
        yield dict(type=ARRAY(UINT32, 8),
                   name='unknown',
                   version=(5, 0, 1, 7))  # SPEC
    attributes = staticmethod(attributes)


class BinData(RecordModel):
    tagid = HWPTAG_BIN_DATA
    StorageType = Enum(LINK=0, EMBEDDING=1, STORAGE=2)
    CompressionType = Enum(STORAGE_DEFAULT=0, YES=1, NO=2)
    AccessState = Enum(NEVER=0, OK=1, FAILED=2, FAILED_IGNORED=3)
    Flags = Flags(INT16,
            0, 3, StorageType, 'storage',
            4, 5, CompressionType, 'compression',
            16, 17, AccessState, 'access')

    def attributes(cls):
        yield cls.Flags, 'flags'
    attributes = classmethod(attributes)

    key_attribute = 'flags'
    submodels = dict()
    def concrete_type_by_attribute(cls, flags):
        return cls.submodels.get(flags.storage)
    concrete_type_by_attribute = classmethod(concrete_type_by_attribute)


class BinDataLink(BinData):
    def attributes():
        yield BSTR, 'abspath'
        yield BSTR, 'relpath'
    attributes = staticmethod(attributes)
BinDataLink.__name__ = 'BinData'
BinData.submodels[BinData.StorageType.LINK] = BinDataLink


class BinDataEmbedding(BinData):
    def attributes():
        yield BinStorageId, 'storage_id'
        yield BSTR, 'ext'
    attributes = staticmethod(attributes)
BinDataEmbedding.__name__ = 'BinData'
BinData.submodels[BinData.StorageType.EMBEDDING] = BinDataEmbedding


class BinDataStorage(BinData):
    def attributes():
        yield BinStorageId, 'storage_id'
    attributes = staticmethod(attributes)
BinDataStorage.__name__ = 'BinData'
BinData.submodels[BinData.StorageType.STORAGE] = BinDataStorage


class BinStorageId(UINT16):
    pass


class AlternateFont(Struct):
    def attributes():
        yield BYTE, 'kind'
        yield BSTR, 'name'
    attributes = staticmethod(attributes)


class Panose1(Struct):
    def attributes():
        yield BYTE, 'family_kind',
        yield BYTE, 'serif_style',
        yield BYTE, 'weight',
        yield BYTE, 'proportion',
        yield BYTE, 'contrast',
        yield BYTE, 'stroke_variation',
        yield BYTE, 'arm_style',
        yield BYTE, 'letterform',
        yield BYTE, 'midline',
        yield BYTE, 'xheight',
    attributes = staticmethod(attributes)


class FaceName(RecordModel):
    tagid = HWPTAG_FACE_NAME
    Flags = Flags(BYTE,
        5, 'default',
        6, 'metric',
        7, 'alternate',
        )

    def attributes(cls):
        yield cls.Flags, 'has'
        yield BSTR, 'name'

        def has_alternate(context, values):
            return values['has'].alternate
        def has_metric(context, values):
            return values['has'].metric
        def has_default(context, values):
            return values['has'].default
        yield dict(type=AlternateFont, name='alternate_font',
                   condition=has_alternate)
        yield dict(type=Panose1, name='panose1', condition=has_metric)
        yield dict(type=BSTR, name='default_font', condition=has_default)
    attributes = classmethod(attributes)


class COLORREF(int):
    read = staticmethod(INT32.read)
    __slots__ = []

    def __getattr__(self, name):
        if name == 'r':
            return self & 0xff
        elif name == 'g':
            return (self & 0xff00) >> 8
        elif name == 'b':
            return (self & 0xff0000) >> 16
        elif name == 'a':
            return (self & 0xff000000) >> 24
        elif name == 'rgb':
            return self.r, self.g, self.b

    def __str__(self):
        return '#%02x%02x%02x' % (self.r, self.g, self.b)

    def __repr__(self):
        class_name = self.__class__.__name__
        value = '(0x%02x, 0x%02x, 0x%02x)' % self.rgb
        return class_name + value


class Border(Struct):

    # 표 20 테두리선 종류
    StrokeEnum = Enum('none', 'solid', 'dashed', 'dotted', 'dash-dot', 'dash-dot-dot',
                      'long-dash', 'large-dot',
                      'double', 'double-2', 'double-3', 'triple',
                      'wave', 'double-wave',
                      'inset', 'outset', 'groove', 'ridge')
    StrokeType = Flags(UINT8,
                       0, 4, StrokeEnum, 'stroke_type')

    # 표 21 테두리선 굵기
    widths = {'0.1mm': 0,
              '0.12mm': 1,
              '0.15mm': 2,
              '0.2mm': 3,
              '0.25mm': 4,
              '0.3mm': 5,
              '0.4mm': 6,
              '0.5mm': 7,
              '0.6mm': 8,
              '0.7mm': 9,
              '1.0mm': 10,
              '1.5mm': 11,
              '2.0mm': 12,
              '3.0mm': 13,
              '4.0mm': 14,
              '5.0mm': 15}
    WidthEnum = Enum(**widths)
    Width = Flags(UINT8,
                  0, 4, WidthEnum, 'width')

    def attributes(cls):
        yield cls.StrokeType, 'stroke_flags',
        yield cls.Width, 'width_flags',
        yield COLORREF, 'color',
    attributes = classmethod(attributes)


class Fill(Struct):
    pass


class FillNone(Fill):
    def attributes():
        yield UINT32, 'size',  # SPEC is confusing
    attributes = staticmethod(attributes)


class FillColorPattern(Fill):
    ''' 표 23 채우기 정보 '''
    PatternTypeEnum = Enum(NONE=255, HORIZONTAL=0, VERTICAL=1, BACKSLASH=2,
                           SLASH=3, GRID=4, CROSS=5)
    PatternTypeFlags = Flags(INT32,
            0, 7, PatternTypeEnum, 'pattern_type')

    def attributes(cls):
        yield COLORREF, 'background_color',
        yield COLORREF, 'pattern_color',
        yield cls.PatternTypeFlags, 'pattern_type_flags',
        # TODO 이것이 존재하는 버젼이 실제로 있는지 확인 필요
        yield dict(type=UINT32, name='unknown', version=(5, 0, 0, 6))
    attributes = classmethod(attributes)


class FillGradation(Fill):
    def attributes():
        yield BYTE,   'type',
        yield UINT32, 'shear',
        yield ARRAY(UINT32, 2), 'center'
        yield UINT32, 'blur',
        yield N_ARRAY(UINT32, COLORREF), 'colors',
        yield UINT32, 'shape',
        yield BYTE,   'blur_center',
    attributes = staticmethod(attributes)


class BorderFill(RecordModel):
    tagid = HWPTAG_BORDER_FILL

    Fill = Enum(NONE=0, COLORPATTERN=1, GRADATION=4)
    FillFlags = Flags(UINT32,
                      0, 7, Fill, 'fill_type')

    def attributes(cls):
        yield UINT16, 'attr'
        yield Border, 'left',
        yield Border, 'right',
        yield Border, 'top',
        yield Border, 'bottom',
        yield Border, 'diagonal'
        yield cls.FillFlags, 'fillflags'
        def fill_colorpattern(context, values):
            return values['fillflags'].fill_type == cls.Fill.COLORPATTERN
        def fill_gradation(context, values):
            return values['fillflags'].fill_type == cls.Fill.GRADATION
        yield dict(type=FillColorPattern, name='fill',
                   condition=fill_colorpattern)
        yield dict(type=FillGradation, name='fill', condition=fill_gradation)
    attributes = classmethod(attributes)


def LanguageStruct(name, basetype):
    def attributes():
        for lang in ('ko', 'en', 'cn', 'jp', 'other', 'symbol', 'user'):
            yield basetype, lang
    attributes = staticmethod(attributes)
    return StructType(name, (Struct,), dict(basetype=basetype,
                                            attributes=attributes))


class CharShape(RecordModel):
    tagid = HWPTAG_CHAR_SHAPE

    Underline = Enum(NONE=0, UNDERLINE=1, UNKNOWN=2, UPPERLINE=3)
    Flags = Flags(UINT32,
            0, 'italic',
            1, 'bold',
            2, 3, Underline, 'underline',
            4, 7, 'underline_style',
            8, 10, 'outline',
            11, 13, 'shadow')

    def attributes(cls):
        yield LanguageStruct('FontFace', WORD), 'font_face',
        yield LanguageStruct('LetterWidthExpansion', UINT8),\
                'letter_width_expansion'
        yield LanguageStruct('LetterSpacing', INT8), 'letter_spacing'
        yield LanguageStruct('RelativeSize', INT8), 'relative_size'
        yield LanguageStruct('Position', INT8), 'position'
        yield INT32, 'basesize',
        yield cls.Flags, 'charshapeflags',
        yield ARRAY(INT8, 2), 'shadow_space'
        yield COLORREF, 'text_color',
        yield COLORREF, 'underline_color',
        yield COLORREF, 'shade_color',
        yield COLORREF, 'shadow_color',
        #yield UINT16, 'borderfill_id',        # DIFFSPEC
        #yield COLORREF, 'strikeoutColor',    # DIFFSPEC
    attributes = classmethod(attributes)


class TabDef(RecordModel):
    tagid = HWPTAG_TAB_DEF

    def attributes():
        # SPEC is confusing
        yield dict(type=UINT32, name='unknown1', version=(5, 0, 1, 7))
        yield dict(type=UINT32, name='unknown2', version=(5, 0, 1, 7))
        #yield UINT32, 'attr',
        #yield UINT16, 'count',
        #yield HWPUNIT, 'pos',
        #yield UINT8, 'kind',
        #yield UINT8, 'fillType',
        #yield UINT16, 'reserved',
    attributes = staticmethod(attributes)


class Numbering(RecordModel):
    tagid = HWPTAG_NUMBERING
    Align = Enum(LEFT=0, CENTER=1, RIGHT=2)
    DistanceType = Enum(RATIO=0, VALUE=1)
    Flags = Flags(UINT32,
        0, 1, Align, 'paragraph_align',
        2, 'auto_width',
        3, 'auto_dedent',
        4, DistanceType, 'distance_to_body_type',
        )

    def attributes(cls):
        yield cls.Flags, 'flags'
        yield HWPUNIT16, 'width_correction'
        yield HWPUNIT16, 'distance_to_body'
        yield UINT32, 'charshape_id'  # SPEC ?????
    attributes = classmethod(attributes)


class Bullet(RecordModel):
    tagid = HWPTAG_BULLET


class ParaShape(RecordModel):
    ''' 4.1.10. 문단 모양 '''
    tagid = HWPTAG_PARA_SHAPE
    LineSpacingType = Enum(RATIO=0, FIXED=1, SPACEONLY=2, MINIMUM=3)
    Align = Enum(BOTH=0, LEFT=1, RIGHT=2, CENTER=3, DISTRIBUTE=4,
                 DISTRIBUTE_SPACE=5)
    VAlign = Enum(FONT=0, TOP=1, CENTER=2, BOTTOM=3)
    LineBreakAlphabet = Enum(WORD=0, HYPHEN=1, CHAR=2)
    LineBreakHangul = Enum(WORD=0, CHAR=1)
    HeadShape = Enum(NONE=0, OUTLINE=1, NUMBER=2, BULLET=3)
    Flags = Flags(UINT32,
            0, 1, LineSpacingType, 'linespacing_type',
            2, 4, Align, 'align',
            5, 6, LineBreakAlphabet, 'linebreak_alphabet',
            7, LineBreakHangul, 'linebreak_hangul',
            8, 'use_paper_grid',
            9, 15, 'minimum_space',  # 공백 최소값
            16, 'protect_single_line',  # 외톨이줄 보호
            17, 'with_next_paragraph',  # 다음 문단과 함께
            18, 'protect',  # 문단 보호
            19, 'start_new_page',  # 문단 앞에서 항상 쪽 나눔
            20, 21, VAlign, 'valign',
            22, 'lineheight_along_fontsize',  # 글꼴에 어울리는 줄 높이
            23, 24, HeadShape, 'head_shape',  # 문단 머리 모양
            25, 27, 'level',  # 문단 수준
            28, 'linked_border',  # 문단 테두리 연결 여부
            29, 'ignore_margin',  # 문단 여백 무시
            30, 'tail_shape',  # 문단 꼬리 모양
            )
    Flags2 = dataio.Flags(UINT32,
            0, 1, 'in_single_line',
            2, 3, 'reserved',
            4, 'autospace_alphabet',
            5, 'autospace_number',
            )
    Flags3 = dataio.Flags(UINT32,
            0, 4, LineSpacingType, 'linespacing_type3'
            )

    def attributes(cls):
        yield cls.Flags, 'parashapeflags',
        yield INT32,  'doubled_margin_left',   # 1/7200 * 2 # DIFFSPEC
        yield INT32,  'doubled_margin_right',  # 1/7200 * 2
        yield SHWPUNIT,  'indent',
        yield INT32,  'doubled_margin_top',    # 1/7200 * 2
        yield INT32,  'doubled_margin_bottom',  # 1/7200 * 2
        yield SHWPUNIT,  'linespacing',
        yield UINT16, 'tabdef_id',
        yield UINT16, 'numbering_bullet_id',
        yield UINT16, 'borderfill_id',
        yield HWPUNIT16,  'border_left',
        yield HWPUNIT16,  'border_right',
        yield HWPUNIT16,  'border_top',
        yield HWPUNIT16,  'border_bottom',
        yield dict(type=cls.Flags2, name='flags2', version=(5, 0, 1, 7))
        #yield cls.Flags3, 'flags3',   # DIFFSPEC
        #yield UINT32, 'lineSpacing',  # DIFFSPEC
    attributes = classmethod(attributes)


class Style(RecordModel):
    tagid = HWPTAG_STYLE

    def attributes():
        yield BSTR, 'local_name',
        yield BSTR, 'name',
        yield BYTE, 'attr',
        yield BYTE, 'next_style_id',
        yield INT16, 'lang_id',
        yield UINT16, 'parashape_id',
        yield UINT16, 'charshape_id',
        yield dict(type=UINT16, name='unknown', version=(5, 0, 0, 5))  # SPEC
    attributes = staticmethod(attributes)


class DocData(RecordModel):
    tagid = HWPTAG_DOC_DATA


class DistributeDocData(RecordModel):
    tagid = HWPTAG_DISTRIBUTE_DOC_DATA


class CompatibleDocument(RecordModel):
    tagid = HWPTAG_COMPATIBLE_DOCUMENT
    Target = Enum(DEFAULT=0, HWP2007=1, MSWORD=2)
    Flags = dataio.Flags(UINT32,
            0, 1, 'target',
            )

    def attributes(cls):
        yield cls.Flags, 'flags'
    attributes = classmethod(attributes)


class LayoutCompatibility(RecordModel):
    tagid = HWPTAG_LAYOUT_COMPATIBILITY

    def attributes():
        yield UINT32, 'char',
        yield UINT32, 'paragraph',
        yield UINT32, 'section',
        yield UINT32, 'object',
        yield UINT32, 'field',
    attributes = staticmethod(attributes)


class CHID(str):
    # Common controls
    GSO = 'gso '
    TBL = 'tbl '
    LINE = '$lin'
    RECT = '$rec'
    ELLI = '$ell'
    ARC = '$arc'
    POLY = '$pol'
    CURV = '$cur'
    EQED = 'eqed'
    PICT = '$pic'
    OLE = '$ole'
    CONTAINER = '$con'

    # Controls
    SECD = 'secd'
    COLD = 'cold'
    HEADER = 'head'
    FOOTER = 'foot'
    FN = 'fn  '
    EN = 'en  '
    ATNO = 'atno'
    NWNO = 'nwno'
    PGHD = 'pghd'
    PGCT = 'pgct'
    PGNP = 'pgnp'
    IDXM = 'idxm'
    BOKM = 'bokm'
    TCPS = 'tcps'
    TDUT = 'tdut'
    TCMT = 'tcmt'

    # Field starts
    UNK = '%unk'
    DTE = '%dte'
    #...
    HLK = '%hlk'

    def decode(bytes):
        return bytes[3] + bytes[2] + bytes[1] + bytes[0]
    decode = staticmethod(decode)

    def read(cls, f, context=None):
        bytes = readn(f, 4)
        return cls.decode(bytes)
    read = classmethod(read)

    def __new__(cls, *args):
        return str.__new__(cls, *args)


control_models = dict()


class ControlType(RecordModelType):
    def __init__(cls, name, bases, attrs):
        super(ControlType, cls).__init__(name, bases, attrs)
        if 'chid' in attrs:
            chid = attrs['chid']
            existing = control_models.get(chid)
            assert not chid in control_models,\
                    ('duplicated ControlType instances for chid \'%s\':'
                     + 'new=%s, existing=%s' % (chid, name, existing.__name__))
            control_models[chid] = cls


class Control(RecordModel):
    __metaclass__ = ControlType
    tagid = HWPTAG_CTRL_HEADER

    def attributes():
        yield CHID, 'chid'
    attributes = staticmethod(attributes)

    key_attribute = 'chid'

    def concrete_type_by_attribute(cls, chid):
        return control_models.get(chid)
    concrete_type_by_attribute = classmethod(concrete_type_by_attribute)


class Margin(Struct):
    def attributes():
        yield HWPUNIT16, 'left'
        yield HWPUNIT16, 'right'
        yield HWPUNIT16, 'top'
        yield HWPUNIT16, 'bottom'
    attributes = staticmethod(attributes)


class CommonControl(Control):
    Flow = Enum(FLOAT=0, BLOCK=1, BACK=2, FRONT=3)
    TextSide = Enum(BOTH=0, LEFT=1, RIGHT=2, LARGER=3)
    VRelTo = Enum(PAPER=0, PAGE=1, PARAGRAPH=2)
    HRelTo = Enum(PAPER=0, PAGE=1, COLUMN=2, PARAGRAPH=3)
    VAlign = Enum(TOP=0, MIDDLE=1, BOTTOM=2)
    HAlign = Enum(LEFT=0, CENTER=1, RIGHT=2, INSIDE=3, OUTSIDE=4)
    WidthRelTo = Enum(PAPER=0, PAGE=1, COLUMN=2, PARAGRAPH=3, ABSOLUTE=4)
    HeightRelTo = Enum(PAPER=0, PAGE=1, ABSOLUTE=2)
    NumberCategory = Enum(NONE=0, FIGURE=1, TABLE=2, EQUATION=3)

    CommonControlFlags = dataio.Flags(UINT32,
            0, 'inline',
            2, 'affect_line_spacing',
            3, 4, VRelTo, 'vrelto',
            5, 7, VAlign, 'valign',
            8, 9, HRelTo, 'hrelto',
            10, 12, HAlign, 'halign',
            13, 'restrict_in_page',
            14, 'overlap_others',
            15, 17, WidthRelTo, 'width_relto',
            18, 19, HeightRelTo, 'height_relto',
            20, 'protect_size_when_vrelto_paragraph',
            21, 23, Flow, 'flow',
            24, 25, TextSide, 'text_side',
            26, 27, NumberCategory, 'number_category'
            )

    MARGIN_LEFT = 0
    MARGIN_RIGHT = 1
    MARGIN_TOP = 2
    MARGIN_BOTTOM = 3

    def attributes(cls):
        yield cls.CommonControlFlags, 'flags',
        yield SHWPUNIT, 'y',    # DIFFSPEC
        yield SHWPUNIT, 'x',    # DIFFSPEC
        yield HWPUNIT, 'width',
        yield HWPUNIT, 'height',
        yield INT16, 'z_order',
        yield INT16, 'unknown1',
        yield Margin, 'margin',
        yield UINT32, 'instance_id',
        yield dict(type=INT16, name='unknown2', version=(5, 0, 0, 5))
        yield dict(type=BSTR, name='description', version=(5, 0, 0, 5))
    attributes = classmethod(attributes)


class TableControl(CommonControl):
    chid = CHID.TBL

    def alternate_child_type(cls, attributes, context, child):
        child_context, child_model = child
        if child_model['type'] is TableBody:
            context['table_body'] = True
        elif child_model['type'] is ListHeader:
            if context.get('table_body', False):
                return TableCell
            else:
                return TableCaption
    alternate_child_type = classmethod(alternate_child_type)


class ListHeader(RecordModel):
    tagid = HWPTAG_LIST_HEADER
    Flags = Flags(UINT32,
        0, 2, 'textdirection',
        3, 4, 'linebreak',
        5, 6, 'valign',
        )
    VALIGN_MASK     = 0x60
    VALIGN_TOP      = 0x00
    VALIGN_MIDDLE   = 0x20
    VALIGN_BOTTOM   = 0x40

    def attributes(cls):
        yield UINT16, 'paragraphs',
        yield UINT16, 'unknown1',
        yield cls.Flags, 'listflags',
    attributes = classmethod(attributes)


class PageDef(RecordModel):
    tagid = HWPTAG_PAGE_DEF
    Orientation = Enum(PORTRAIT=0, LANDSCAPE=1)
    BookBinding = Enum(LEFT=0, RIGHT=1, TOP=2, BOTTOM=3)
    Flags = Flags(UINT32,
                0, Orientation, 'orientation',
                1, 2, BookBinding, 'bookbinding'
                )

    def attributes(cls):
        yield HWPUNIT, 'width',
        yield HWPUNIT, 'height',
        yield HWPUNIT, 'left_offset',
        yield HWPUNIT, 'right_offset',
        yield HWPUNIT, 'top_offset',
        yield HWPUNIT, 'bottom_offset',
        yield HWPUNIT, 'header_offset',
        yield HWPUNIT, 'footer_offset',
        yield HWPUNIT, 'bookbinding_offset',
        yield cls.Flags, 'attr',
        #yield UINT32, 'attr',
    attributes = classmethod(attributes)

    def getDimension(self):
        width = HWPUNIT(self.paper_width - self.offsetLeft - self.offsetRight)
        height = HWPUNIT(self.paper_height
                         - (self.offsetTop + self.offsetHeader)
                         - (self.offsetBottom + self.offsetFooter))
        if self.attr.landscape:
            return (height, width)
        else:
            return (width, height)
    dimension = property(getDimension)

    def getHeight(self):
        if self.attr.landscape:
            width = HWPUNIT(self.paper_width - self.offsetLeft -
                            self.offsetRight)
            return width
        else:
            height = HWPUNIT(self.paper_height
                             - (self.offsetTop + self.offsetHeader)
                             - (self.offsetBottom + self.offsetFooter))
            return height
    height = property(getHeight)

    def getWidth(self):
        if self.attr.landscape:
            height = HWPUNIT(self.paper_height
                             - (self.offsetTop + self.offsetHeader)
                             - (self.offsetBottom + self.offsetFooter))
            return height
        else:
            width = HWPUNIT(self.paper_width - self.offsetLeft -
                            self.offsetRight)
            return width
    width = property(getWidth)


class FootnoteShape(RecordModel):
    tagid = HWPTAG_FOOTNOTE_SHAPE
    Flags = Flags(UINT32,
        )

    def attributes(cls):
        yield cls.Flags, 'flags'
        yield WCHAR, 'usersymbol'
        yield WCHAR, 'prefix'
        yield WCHAR, 'suffix'
        yield UINT16, 'starting_number'
        yield HWPUNIT16, 'splitter_length'
        yield HWPUNIT16, 'splitter_unknown'
        yield HWPUNIT16, 'splitter_margin_top'
        yield HWPUNIT16, 'splitter_margin_bottom'
        yield HWPUNIT16, 'notes_spacing'
        yield Border.StrokeType, 'splitter_stroke_type'
        yield Border.Width, 'splitter_width'
        yield dict(type=COLORREF, name='splitter_color', version=(5,0,0,6))
    attributes = classmethod(attributes)


class PageBorderFill(RecordModel):
    tagid = HWPTAG_PAGE_BORDER_FILL
    RelativeTo = Enum(BODY=0, PAPER=1)
    FillArea = Enum(PAPER=0, PAGE=1, BORDER=2)
    Flags = Flags(UINT32,
        0, RelativeTo, 'relative_to',
        1, 'include_header',
        2, 'include_footer',
        3, 4, FillArea, 'fill',
        )

    def attributes(cls):
        yield cls.Flags, 'flags'
        yield Margin, 'margin'
        yield UINT16, 'borderfill_id'
    attributes = classmethod(attributes)


class TableCaption(ListHeader):
    Position = Enum(LEFT=0, RIGHT=1, TOP=2, BOTTOM=3)
    Flags = Flags(UINT32,
                0, 1, Position, 'position',
                2, 'include_margin',
                )

    def attributes(cls):
        yield cls.Flags, 'flags',
        yield HWPUNIT, 'width',
        yield HWPUNIT16, 'separation',  # 캡션과 틀 사이 간격
        yield HWPUNIT, 'maxsize',
    attributes = classmethod(attributes)


class TableCell(ListHeader):
    def attributes():
        yield UINT16, 'col',
        yield UINT16, 'row',
        yield UINT16, 'colspan',
        yield UINT16, 'rowspan',
        yield HWPUNIT, 'width',
        yield HWPUNIT, 'height',
        yield Margin, 'padding',
        yield UINT16, 'borderfill_id',
        yield HWPUNIT, 'unknown_width',
    attributes = staticmethod(attributes)


class TableBody(RecordModel):
    tagid = HWPTAG_TABLE
    Split = Enum(NONE=0, BY_CELL=1, SPLIT=2)
    Flags = Flags(UINT32,
                0, 1, Split, 'split_page',
                2, 'repeat_header',
                )
    ZoneInfo = ARRAY(UINT16, 5)

    def attributes(cls):
        yield cls.Flags, 'flags'
        yield UINT16, 'rows'
        yield UINT16, 'cols'
        yield HWPUNIT16, 'cellspacing'
        yield Margin, 'padding'
        def rowcols_type(context, values):
            return ARRAY(UINT16, values['rows'])
        yield dict(type_func=rowcols_type,
                   name='rowcols')
        yield UINT16, 'borderfill_id'
        yield dict(type=N_ARRAY(UINT16, cls.ZoneInfo),
                   name='validZones',
                   version=(5, 0, 0, 7))
    attributes = classmethod(attributes)


class Paragraph(RecordModel):
    tagid = HWPTAG_PARA_HEADER

    SplitFlags = Flags(BYTE,
            0, 'new_section',
            1, 'new_columnsdef',
            2, 'new_page',
            3, 'new_column',
            )
    ControlMask = Flags(UINT32,
            2, 'unknown1',
            11, 'control',
            21, 'new_number',
            )
    Flags = Flags(UINT32,
            31, 'unknown',
            0, 30, 'chars',
            )

    def attributes(cls):
        yield cls.Flags, 'text',
        yield cls.ControlMask, 'controlmask',
        yield UINT16, 'parashape_id',
        yield BYTE, 'style_id',
        yield cls.SplitFlags, 'split',
        yield UINT16, 'charshapes',
        yield UINT16, 'rangetags',
        yield UINT16, 'linesegs',
        yield UINT32, 'instance_id',
    attributes = classmethod(attributes)


class ControlChar(object):
    class CHAR(object):
        size = 1

    class INLINE(object):
        size = 8

    class EXTENDED(object):
        size = 8
    chars = {
            0x00: ('NULL', CHAR),
            0x01: ('CTLCHR01', EXTENDED),
            0x02: ('SECTION_COLUMN_DEF', EXTENDED),
            0x03: ('FIELD_START', EXTENDED),
            0x04: ('FIELD_END', INLINE),
            0x05: ('CTLCHR05', INLINE),
            0x06: ('CTLCHR06', INLINE),
            0x07: ('CTLCHR07', INLINE),
            0x08: ('TITLE_MARK', INLINE),
            0x09: ('TAB', INLINE),
            0x0a: ('LINE_BREAK', CHAR),
            0x0b: ('DRAWING_TABLE_OBJECT', EXTENDED),
            0x0c: ('CTLCHR0C', EXTENDED),
            0x0d: ('PARAGRAPH_BREAK', CHAR),
            0x0e: ('CTLCHR0E', EXTENDED),
            0x0f: ('HIDDEN_EXPLANATION', EXTENDED),
            0x10: ('HEADER_FOOTER', EXTENDED),
            0x11: ('FOOT_END_NOTE', EXTENDED),
            0x12: ('AUTO_NUMBER', EXTENDED),
            0x13: ('CTLCHR13', INLINE),
            0x14: ('CTLCHR14', INLINE),
            0x15: ('PAGE_CTLCHR', EXTENDED),
            0x16: ('BOOKMARK', EXTENDED),
            0x17: ('CTLCHR17', EXTENDED),
            0x18: ('HYPHEN', CHAR),
            0x1e: ('NONBREAK_SPACE', CHAR),
            0x1f: ('FIXWIDTH_SPACE', CHAR),
    }
    names = dict((unichr(code), name) for code, (name, kind) in chars.items())
    kinds = dict((unichr(code), kind) for code, (name, kind) in chars.items())

    def _populate(cls):
        for ch, name in cls.names.items():
            setattr(cls, name, ch)
    _populate = classmethod(_populate)
    import re
    regex = re.compile('[\x00-\x1f]\x00')

    def find(cls, data, start_idx):
        while True:
            m = cls.regex.search(data, start_idx)
            if m is not None:
                i = m.start()
                if i & 1 == 1:
                    start_idx = i + 1
                    continue
                char = unichr(ord(data[i]))
                size = cls.kinds[char].size
                return i, i + (size * 2)
        data_len = len(data)
        return data_len, data_len
    find = classmethod(find)

    def decode_bytes(cls, bytes):
        code = UINT16.decode(bytes[0:2])
        ch = unichr(code)
        if cls.kinds[ch].size == 8:
            bytes = bytes[2:2+12]
            if ch == ControlChar.TAB:
                s = StringIO(bytes)
                param = dict(width=UINT32.read(s),
                             unknown0=UINT8.read(s),
                             unknown1=UINT8.read(s),
                             unknown2=s.read())
                return dict(code=code, param=param)
            else:
                chid = CHID.decode(bytes[0:4])
                param = bytes[4:12]
                return dict(code=code, chid=chid, param=param)
        else:
            return dict(code=code)
    decode_bytes = classmethod(decode_bytes)

    def get_kind_by_code(cls, code):
        ch = unichr(code)
        return cls.kinds[ch]
    get_kind_by_code = classmethod(get_kind_by_code)

    def get_name_by_code(cls, code):
        ch = unichr(code)
        return cls.names.get(ch, 'CTLCHR%02x' % code)
    get_name_by_code = classmethod(get_name_by_code)

ControlChar._populate()


class Text(object):
    pass


class ParaTextChunks(list):
    __metaclass__ = CompoundType

    def read(cls, f, context):
        bytes = f.read()
        return [x for x in cls.parse_chunks(bytes)]
    read = classmethod(read)

    def parse_chunks(bytes):
        size = len(bytes)
        idx = 0
        while idx < size:
            ctrlpos, ctrlpos_end = ControlChar.find(bytes, idx)
            if idx < ctrlpos:
                text = bytes[idx:ctrlpos].decode('utf-16le', 'replace')
                yield (idx / 2, ctrlpos / 2), text
            if ctrlpos < ctrlpos_end:
                cch = ControlChar.decode_bytes(bytes[ctrlpos:ctrlpos_end])
                yield (ctrlpos / 2, ctrlpos_end / 2), cch
            idx = ctrlpos_end
    parse_chunks = staticmethod(parse_chunks)


class ParaText(RecordModel):
    tagid = HWPTAG_PARA_TEXT

    def attributes():
        yield ParaTextChunks, 'chunks'
    attributes = staticmethod(attributes)


class ParaCharShapeList(list):
    __metaclass__ = ArrayType
    itemtype = ARRAY(UINT16, 2)

    def read(cls, f, context):
        bytes = f.read()
        return cls.decode(bytes, context)
    read = classmethod(read)

    def decode(payload, context=None):
        import struct
        fmt = 'II'
        unitsize = struct.calcsize('<'+fmt)
        unitcount = len(payload) / unitsize
        values = struct.unpack('<'+(fmt*unitcount), payload)
        return list(tuple(values[i*2:i*2+2]) for i in range(0, unitcount))
    decode = staticmethod(decode)


class ParaCharShape(RecordModel):
    tagid = HWPTAG_PARA_CHAR_SHAPE

    def attributes():
        yield ParaCharShapeList, 'charshapes'
    attributes = staticmethod(attributes)


class LineSeg(Struct):
    Flags = Flags(UINT16,
            4, 'indented')

    def attributes(cls):
        yield INT32, 'chpos',
        yield SHWPUNIT, 'y',
        yield SHWPUNIT, 'height',
        yield SHWPUNIT, 'height2',
        yield SHWPUNIT, 'height85',
        yield SHWPUNIT, 'space_below',
        yield SHWPUNIT, 'x',
        yield SHWPUNIT, 'width'
        yield UINT16, 'a8'
        yield cls.Flags, 'flags'
    attributes = classmethod(attributes)


class ParaLineSegList(list):
    __metaclass__ = ArrayType
    itemtype = LineSeg

    def read(cls, f, context):
        payload = context['stream'].read()
        return cls.decode(context, payload)
    read = classmethod(read)

    def decode(cls, context, payload):
        from itertools import izip
        import struct
        unitfmt = 'iiiiiiiiHH'
        unitsize = struct.calcsize('<'+unitfmt)
        unitcount = len(payload) / unitsize
        values = struct.unpack('<'+unitfmt*unitcount, payload)
        names = ['chpos', 'y', 'height', 'height2', 'height85', 'space_below', 'x', 'width', 'a8', 'flags']
        x = list(dict(izip(names, tuple(values[i*10:i*10+10])))
                 for i in range(0, unitcount))
        for d in x:
            d['flags'] = LineSeg.Flags(d['flags'])
        return x
    decode = classmethod(decode)


class ParaLineSeg(RecordModel):
    tagid = HWPTAG_PARA_LINE_SEG

    def attributes(cls):
        yield ParaLineSegList, 'linesegs'
    attributes = classmethod(attributes)


class ParaRangeTag(RecordModel):
    tagid = HWPTAG_PARA_RANGE_TAG

    def attributes():
        yield UINT32, 'start'
        yield UINT32, 'end'
        yield UINT32, 'tag'
        # TODO: SPEC
    attributes = staticmethod(attributes)


class GShapeObjectControl(CommonControl):
    chid = CHID.GSO

    def alternate_child_type(cls, attributes, context,
                    (child_context, child_model)):
        # TODO: ListHeader to Caption
        pass
    alternate_child_type = classmethod(alternate_child_type)


class Matrix(Struct):
    ''' 2D Transform Matrix

    [a c e][x]
    [b d f][y]
    [0 0 1][1]
    '''
    def attributes():
        yield DOUBLE, 'a'
        yield DOUBLE, 'c'
        yield DOUBLE, 'e'
        yield DOUBLE, 'b'
        yield DOUBLE, 'd'
        yield DOUBLE, 'f'
    attributes = staticmethod(attributes)


class ScaleRotationMatrix(Struct):
    def attributes():
        yield Matrix, 'scaler',
        yield Matrix, 'rotator',
    attributes = staticmethod(attributes)


class ShapeComponent(RecordModel):
    ''' 4.2.9.2 그리기 개체 '''
    tagid = HWPTAG_SHAPE_COMPONENT
    FillFlags = Flags(UINT16,
            8, 'fill_colorpattern',
            9, 'fill_image',
            10, 'fill_gradation',
            )
    Flags = Flags(UINT32,
            0, 'flip'
            )

    def attributes(cls):

        def parent_must_be_gso(context, values):
            # GSO-child ShapeComponent specific:
            # it may be a GSO model's attribute, e.g. 'child_chid'
            if 'parent' in context:
                parent_context, parent_model = context['parent']
                return parent_model['type'] is GShapeObjectControl

        yield dict(type=CHID, name='chid0', condition=parent_must_be_gso)

        yield CHID, 'chid'
        yield SHWPUNIT, 'x_in_group'
        yield SHWPUNIT, 'y_in_group'
        yield WORD, 'level_in_group'
        yield WORD, 'local_version'
        yield SHWPUNIT, 'initial_width'
        yield SHWPUNIT, 'initial_height'
        yield SHWPUNIT, 'width'
        yield SHWPUNIT, 'height'
        yield cls.Flags, 'flags'
        yield WORD, 'angle'
        yield Coord, 'rotation_center'
        yield WORD, 'scalerotations_count'
        yield Matrix, 'translation'

        def scalerotations_type(context, values):
            ''' ARRAY(ScaleRotationMatrix, scalerotations_count) '''
            return ARRAY(ScaleRotationMatrix, values['scalerotations_count'])
        yield dict(type_func=scalerotations_type, name='scalerotations')

        def chid_is_container(context, values):
            return values['chid'] == CHID.CONTAINER
        yield dict(type=N_ARRAY(WORD, CHID),
                   name='controls',
                   condition=chid_is_container)

        def chid_is_rect(context, values):
            return values['chid'] == CHID.RECT
        def chid_is_rect_and_fill_colorpattern(context, values):
            return (values['chid'] == CHID.RECT and
                    values['fill_flags'].fill_colorpattern)
        def chid_is_rect_and_fill_gradation(context, values):
            return (values['chid'] == CHID.RECT and
                    values['fill_flags'].fill_gradation)
        yield dict(type=BorderLine, name='border', condition=chid_is_rect)
        yield dict(type=cls.FillFlags, name='fill_flags',
                   condition=chid_is_rect)
        yield dict(type=UINT16, name='unknown', condition=chid_is_rect)
        yield dict(type=UINT8, name='unknown1', condition=chid_is_rect)
        yield dict(type=FillColorPattern, name='colorpattern',
                   condition=chid_is_rect_and_fill_colorpattern)
        yield dict(type=FillGradation, name='gradation',
                   condition=chid_is_rect_and_fill_gradation)

        def chid_is_line(context, values):
            return values['chid'] == CHID.LINE
        yield dict(type=BorderLine, name='line',
                   condition=chid_is_line)
    attributes = classmethod(attributes)

    def alternate_child_type(cls, attributes, context,
                    (child_context, child_model)):
        if child_model['type'] is ListHeader:
            return TextboxParagraphList
    alternate_child_type = classmethod(alternate_child_type)


class TextboxParagraphList(ListHeader):
    def attributes():
        yield Margin, 'padding'
        yield HWPUNIT, 'maxwidth'
    attributes = staticmethod(attributes)


class Coord(Struct):
    def attributes():
        yield SHWPUNIT, 'x'
        yield SHWPUNIT, 'y'
    attributes = staticmethod(attributes)


class ShapeLine(RecordModel):
    tagid = HWPTAG_SHAPE_COMPONENT_LINE

    def attributes():
        yield ARRAY(Coord, 2), 'coords'
        yield UINT16, 'attr'
    attributes = staticmethod(attributes)


class ShapeRectangle(RecordModel):
    tagid = HWPTAG_SHAPE_COMPONENT_RECTANGLE

    def attributes():
        yield BYTE, 'round',
        yield ARRAY(Coord, 4), 'coords',
    attributes = staticmethod(attributes)


class ShapeEllipse(RecordModel):
    tagid = HWPTAG_SHAPE_COMPONENT_ELLIPSE
    Flags = Flags(UINT32)  # TODO

    def attributes(cls):
        yield cls.Flags, 'flags'
        yield Coord, 'center'
        yield Coord, 'axis1'
        yield Coord, 'axis2'
        yield Coord, 'start1'
        yield Coord, 'end1'
        yield Coord, 'start2'
        yield Coord, 'end2'
    attributes = classmethod(attributes)


class ShapeArc(RecordModel):
    tagid = HWPTAG_SHAPE_COMPONENT_ARC

    def attributes(cls):
        #yield ShapeEllipse.Flags, 'flags' # SPEC
        yield Coord, 'center'
        yield Coord, 'axis1'
        yield Coord, 'axis2'
    attributes = classmethod(attributes)


class ShapePolygon(RecordModel):
    tagid = HWPTAG_SHAPE_COMPONENT_POLYGON

    def attributes(cls):
        yield N_ARRAY(UINT16, Coord), 'points'
    attributes = classmethod(attributes)


class ShapeCurve(RecordModel):
    tagid = HWPTAG_SHAPE_COMPONENT_CURVE

    def attributes(cls):
        yield ARRAY(UINT16, Coord), 'points'
        # TODO: segment type
    attributes = classmethod(attributes)


class ShapeOLE(RecordModel):
    tagid = HWPTAG_SHAPE_COMPONENT_OLE
    # TODO


class PictureInfo(Struct):
    def attributes():
        yield INT8, 'brightness',
        yield INT8, 'contrast',
        yield BYTE, 'effect',
        yield UINT16, 'bindata_id',
    attributes = staticmethod(attributes)


class BorderLine(Struct):
    ''' 표 81. 테두리 선 정보 '''

    StrokeType = Enum('none', 'solid', 'dashed', 'dotted')  # TODO: more types
    LineEnd = Enum('round', 'flat')
    ArrowShape = Enum('none', 'arrow', 'arrow2', 'diamond', 'circle', 'rect',
                      'diamondfilled', 'disc', 'rectfilled')
    ArrowSize = Enum('smallest', 'smaller', 'small', 'abitsmall', 'normal',
                     'abitlarge', 'large', 'larger', 'largest')
    Flags = Flags(UINT32,
            0, 5, StrokeType, 'stroke',
            6, 9, LineEnd, 'line_end',
            10, 15, ArrowShape, 'arrow_start',
            16, 21, ArrowShape, 'arrow_end',
            22, 25, ArrowSize, 'arrow_start_size',
            26, 29, ArrowSize, 'arrow_end_size',
            30, 'arrow_start_fill',
            31, 'arrow_end_fill')

    def attributes(cls):
        yield COLORREF, 'color'
        yield INT32, 'width'
        yield cls.Flags, 'flags'
    attributes = classmethod(attributes)


# HWPML에서의 이름 사용
class ImageRect(Struct):
    ''' 이미지 좌표 정보 '''

    def attributes():
        yield Coord, 'p0'
        yield Coord, 'p1'
        yield Coord, 'p2'
        yield Coord, 'p3'
    attributes = staticmethod(attributes)


# HWPML에서의 이름 사용
class ImageClip(Struct):
    ''' 이미지 자르기 정보 '''

    def attributes():
        yield SHWPUNIT, 'left',
        yield SHWPUNIT, 'top',
        yield SHWPUNIT, 'right',
        yield SHWPUNIT, 'bottom',
    attributes = staticmethod(attributes)


class ShapePicture(RecordModel):
    ''' 4.2.9.4. 그림 개체 '''
    tagid = HWPTAG_SHAPE_COMPONENT_PICTURE

    def attributes():
        yield BorderLine, 'border'
        yield ImageRect, 'rect',
        yield ImageClip, 'clip',
        yield Margin, 'padding',
        yield PictureInfo, 'picture',
        # DIFFSPEC
            # BYTE, 'transparency',
            # UINT32, 'instanceId',
            # PictureEffect, 'effect',
    attributes = staticmethod(attributes)


class ShapeContainer(RecordModel):
    tagid = HWPTAG_SHAPE_COMPONENT_CONTAINER
    # TODO


class ShapeTextArt(RecordModel):
    tagid = HWPTAG_SHAPE_COMPONENT_TEXTART
    # TODO


class ControlData(RecordModel):
    tagid = HWPTAG_CTRL_DATA


class EqEdit(RecordModel):
    tagid = HWPTAG_CTRL_EQEDIT
    # TODO


class ForbiddenChar(RecordModel):
    tagid = HWPTAG_FORBIDDEN_CHAR
    # TODO


class SectionDef(Control):
    ''' 4.2.10.1. 구역 정의 '''
    chid = CHID.SECD

    def attributes():
        yield UINT32, 'attr',
        yield HWPUNIT16, 'columnspacing',
        yield ARRAY(HWPUNIT16, 2), 'grid',
        yield HWPUNIT, 'defaultTabStops',
        yield UINT16, 'numbering_shape_id',
        yield UINT16, 'starting_pagenum',
        yield UINT16, 'starting_picturenum',
        yield UINT16, 'starting_tablenum',
        yield UINT16, 'starting_equationnum',
        yield dict(type=UINT32, name='unknown1', version=(5, 0, 1, 7))
        yield dict(type=UINT32, name='unknown2', version=(5, 0, 1, 7))
    attributes = staticmethod(attributes)


class ColumnsDef(Control):
    ''' 4.2.10.2. 단 정의 '''
    chid = CHID.COLD

    Kind = Enum('normal', 'distribute', 'parallel')
    Direction = Enum('l2r', 'r2l', 'both')
    Flags = Flags(UINT16,
            0, 1, Kind, 'kind',
            2, 9, 'count',
            10, 11, Direction, 'direction',
            12, 'same_widths',
            )

    def attributes(cls):
        yield cls.Flags, 'flags'
        yield HWPUNIT16, 'spacing'
        def not_same_widths(context, values):
            return not values['flags'].same_widths
        def column_widths_type(context, values):
            return ARRAY(WORD, values['flags'].count)
        yield dict(name='widths',
                   type_func=column_widths_type,
                   condition=not_same_widths)
        yield UINT16, 'attr2'
        yield Border, 'splitter'
    attributes = classmethod(attributes)


class HeaderFooter(Control):
    ''' 4.2.10.3. 머리말/꼬리말 '''
    Places = Enum(BOTH_PAGES=0, EVEN_PAGE=1, ODD_PAGE=2)
    Flags = Flags(UINT32,
        0, 1, Places, 'places'
    )

    def attributes(cls):
        yield cls.Flags, 'flags'
    attributes = classmethod(attributes)

    class ParagraphList(ListHeader):
        def attributes():
            yield HWPUNIT, 'width'
            yield HWPUNIT, 'height'
            yield BYTE, 'textrefsbitmap'
            yield BYTE, 'numberrefsbitmap'
        attributes = staticmethod(attributes)

    def alternate_child_type(cls, attributes, context,
                    (child_context, child_model)):
        if child_model['type'] is ListHeader:
            return cls.ParagraphList
    alternate_child_type = classmethod(alternate_child_type)


class Header(HeaderFooter):
    ''' 머리말 '''
    chid = CHID.HEADER


class Footer(HeaderFooter):
    ''' 꼬리말 '''
    chid = CHID.FOOTER


class Note(Control):
    ''' 4.2.10.4 미주/각주 '''
    def attributes():
        yield dict(type=UINT32, name='number', version=(5, 0, 0, 6))  # SPEC
    attributes = staticmethod(attributes)


class FootNote(Note):
    ''' 각주 '''
    chid = CHID.FN


class EndNote(Note):
    ''' 미주 '''
    chid = CHID.EN


class NumberingControl(Control):
    Kind = Enum(PAGE=0, FOOTNOTE=1, ENDNOTE=2, PICTURE=3, TABLE=4, EQUATION=5)
    Flags = Flags(UINT32,
            0, 3, Kind, 'kind',
            4, 11, 'footnoteshape',
            12, 'superscript',
            )

    def attributes(cls):
        yield cls.Flags, 'flags',
        yield UINT16, 'number',
    attributes = classmethod(attributes)


class AutoNumbering(NumberingControl):
    ''' 4.2.10.5. 자동 번호 '''
    chid = CHID.ATNO

    def attributes(cls):
        for x in NumberingControl.attributes():
            yield x
        yield WCHAR, 'usersymbol',
        yield WCHAR, 'prefix',
        yield WCHAR, 'suffix',
    attributes = classmethod(attributes)

    def __unicode__(self):
        prefix = u''
        suffix = u''
        if self.flags.kind == self.Kind.FOOTNOTE:
            if self.suffix != u'\x00':
                suffix = self.suffix
        return prefix + unicode(self.number) + suffix


class NewNumbering(NumberingControl):
    ''' 4.2.10.6. 새 번호 지정 '''
    chid = CHID.NWNO


class PageHide(Control):
    ''' 4.2.10.7 감추기 '''
    chid = CHID.PGHD
    Flags = Flags(UINT32,
            0, 'header',
            1, 'footer',
            2, 'basepage',
            3, 'pageborder',
            4, 'pagefill',
            5, 'pagenumber'
            )

    def attributes(cls):
        yield cls.Flags, 'flags'
    attributes = classmethod(attributes)


class PageOddEven(Control):
    ''' 4.2.10.8 홀/짝수 조정 '''
    chid = CHID.PGCT
    OddEven = Enum(BOTH_PAGES=0, EVEN_PAGE=1, ODD_PAGE=2)
    Flags = Flags(UINT32,
        0, 1, 'pages'
        )

    def attributes(cls):
        yield cls.Flags, 'flags'
    attributes = classmethod(attributes)


class PageNumberPosition(Control):
    ''' 4.2.10.9. 쪽 번호 위치 '''
    chid = CHID.PGNP
    Position = Enum(NONE=0,
            TOP_LEFT=1, TOP_CENTER=2, TOP_RIGHT=3,
            BOTTOM_LEFT=4, BOTTOM_CENTER=5, BOTTOM_RIGHT=6,
            OUTSIDE_TOP=7, OUTSIDE_BOTTOM=8,
            INSIDE_TOP=9, INSIDE_BOTTOM=10)
    Flags = Flags(UINT32,
        0, 7, 'shape',
        8, 11, Position, 'position',
        )

    def attributes(cls):
        yield cls.Flags, 'flags'
        yield WCHAR, 'usersymbol'
        yield WCHAR, 'prefix'
        yield WCHAR, 'suffix'
        yield WCHAR, 'dash'
    attributes = classmethod(attributes)


class IndexMarker(Control):
    ''' 4.2.10.10. 찾아보기 표식 '''
    chid = CHID.IDXM

    def attributes():
        yield BSTR, 'keyword1'
        yield BSTR, 'keyword2'
        yield UINT16, 'dummy'
    attributes = staticmethod(attributes)


class BookmarkControl(Control):
    ''' 4.2.10.11. 책갈피 '''
    chid = CHID.BOKM

    def attributes():
        if False:
            yield
    attributes = staticmethod(attributes)

    def alternate_child_type(cls, attributes, context,
                    (child_context, child_model)):
        if child_model['type'] is ControlData:
            return BookmarkControlData
    alternate_child_type = classmethod(alternate_child_type)


class BookmarkControlData(ControlData):
    def attributes():
        yield UINT32, 'unknown1'
        yield UINT32, 'unknown2'
        yield UINT16, 'unknown3'
        yield BSTR, 'name'
    attributes = staticmethod(attributes)


class TCPSControl(Control):
    ''' 4.2.10.12. 글자 겹침 '''
    chid = CHID.TCPS

    def attributes():
        yield BSTR, 'textlength'
        #yield UINT8, 'frameType'
        #yield INT8, 'internalCharacterSize'
        #yield UINT8, 'internalCharacterFold'
        #yield N_ARRAY(UINT8, UINT32), 'characterShapeIds'
    attributes = staticmethod(attributes)


class Dutmal(Control):
    ''' 4.2.10.13. 덧말 '''
    chid = CHID.TDUT
    Position = Enum(ABOVE=0, BELOW=1, CENTER=2)
    Align = Enum(BOTH=0, LEFT=1, RIGHT=2, CENTER=3, DISTRIBUTE=4,
                 DISTRIBUTE_SPACE=5)

    def attributes():
        yield BSTR, 'maintext'
        yield BSTR, 'subtext'
        yield UINT32, 'position'
        yield UINT32, 'fsizeratio'
        yield UINT32, 'option'
        yield UINT32, 'stylenumber'
        yield UINT32, 'align'
    attributes = staticmethod(attributes)


class HiddenComment(Control):
    ''' 4.2.10.14 숨은 설명 '''
    chid = CHID.TCMT

    def attributes():
        if False:
            yield
    attributes = staticmethod(attributes)


class Field(Control):
    ''' 4.2.10.15 필드 시작 '''

    Flags = Flags(UINT32,
            0, 'editableInReadOnly',
            11, 14, 'visitedType',
            15, 'modified',
            )

    def attributes(cls):
        yield cls.Flags, 'flags',
        yield BYTE, 'extra_attr',
        yield BSTR, 'command',
        yield UINT32, 'id',
    attributes = classmethod(attributes)


class FieldUnknown(Field):
    chid = '%unk'


class FieldDate(Field):
    chid = CHID.DTE


class FieldDocDate(Field):
    chid = '%ddt'


class FieldPath(Field):
    chid = '%pat'


class FieldBookmark(Field):
    chid = '%bmk'


class FieldMailMerge(Field):
    chid = '%mmg'


class FieldCrossRef(Field):
    chid = '%xrf'


class FieldFormula(Field):
    chid = '%fmu'


class FieldClickHere(Field):
    chid = '%clk'


class FieldSummary(Field):
    chid = '%smr'


class FieldUserInfo(Field):
    chid = '%usr'


class FieldHyperLink(Field):
    chid = CHID.HLK

    def geturl(self):
        s = self.command.split(';')
        return s[0].replace('\\:', ':')

# TODO: FieldRevisionXXX


class FieldMemo(Field):
    chid = '%%me'


class FieldPrivateInfoSecurity(Field):
    chid = '%cpr'


def _check_tag_models():
    for tagid, name in tagnames.iteritems():
        assert tagid in tag_models, 'RecordModel for %s is missing!' % name
_check_tag_models()


def init_record_parsing_context(base, record):
    ''' Initialize a context to parse the given record

        the initializations includes followings:
        - context = dict(base)
        - context['record'] = record
        - context['stream'] = record payload stream

        `base': the base context, which will be shallow-copied into the new one
        `record': to be parsed
        returns new context
    '''

    context = dict(base, record=record, stream=StringIO(record['payload']))
    model = record
    return context, model


def parse_pass0(base_context, records):
    for record in records:
        yield init_record_parsing_context(base_context, record)


def parse_model(context, model):
    ''' HWPTAG로 모델 결정 후 기본 파싱 '''

    # HWPTAG로 모델 결정
    model['type'] = tag_models.get(model['tagid'], RecordModel)
    model['content'] = dict()

    # 1차 파싱
    model['content'] = parse_model_attributes(model['type'], model['content'], context)

    # 키 속성으로 모델 타입 변경 (예: Control.chid에 따라 TableControl 등으로)
    get_altered_model = getattr(model['type'], 'concrete_type_by_attribute',
                                None)
    if get_altered_model:
        key = model['type'].key_attribute
        altered_model = get_altered_model(model['content'][key])
        if altered_model is not None:
            model['type'] = altered_model
            model['content'] = parse_model_attributes(model['type'], model['content'], context)

    if 'parent' not in context:
        return

    parent = context['parent']
    parent_context, parent_model = parent
    parent_type = parent_model.get('type')
    parent_content = parent_model.get('content')

    alternate_child_type = getattr(parent_type, 'alternate_child_type', None)
    if alternate_child_type:
        alter_type = alternate_child_type(parent_content, parent_context, (context, model))
        if alter_type:
            model['type'] = alter_type
            model['content'] = parse_model_attributes(model['type'], model['content'], context)

    logger.debug('pass2: %s, %s', model['type'], model['content'])


def parse_models_with_parent(context_models):
    from .treeop import prefix_ancestors_from_level
    level_prefixed = ((model['level'], (context, model))
                      for context, model in context_models)
    root_item = (dict(), dict())
    ancestors_prefixed = prefix_ancestors_from_level(level_prefixed, root_item)
    for ancestors, (context, model) in ancestors_prefixed:
        context['parent'] = ancestors[-1]
        parse_model(context, model)
        yield context, model


def parse_models(context, records):
    for context, model in parse_models_intern(context, records):
        yield model


def parse_models_intern(context, records, passes=3):
    context_models = parse_pass0(context, records)
    context_models = parse_models_with_parent(context_models)
    for context, model in context_models:
        stream = context['stream']
        unparsed = stream.read()
        if unparsed:
            model['unparsed'] = unparsed
        yield context, model


def model_to_json(model, *args, **kwargs):
    ''' convert a model to json '''
    from .dataio import dumpbytes
    import simplejson  # TODO: simplejson is for python2.5+
    model = dict(model)
    model['type'] = model['type'].__name__
    record = model
    record['payload'] = list(dumpbytes(record['payload']))
    if 'unparsed' in model:
        model['unparsed'] = list(dumpbytes(model['unparsed']))
    return simplejson.dumps(model, *args, **kwargs)


from . import recordstream


class ModelStream(recordstream.RecordStream):

    def models(self, **kwargs):
        # prepare binmodel parsing context
        kwargs.setdefault('version', self.version)
        try:
            kwargs.setdefault('path', self.path)
        except AttributeError:
            pass
        return parse_models(kwargs, self.records(**kwargs))

    def model(self, idx):
        from .recordstream import nth
        return nth(self.models(), idx)

    def models_json(self, **kwargs):
        from .utils import JsonObjects
        models = self.models(**kwargs)
        return JsonObjects(models, model_to_json)

    def other_formats(self):
        d = super(ModelStream, self).other_formats()
        d['.models'] = self.models_json().open
        return d


class Sections(recordstream.Sections):

    section_class = ModelStream


class Hwp5File(recordstream.Hwp5File):

    docinfo_class = ModelStream
    bodytext_class = Sections


def create_context(file=None, **context):
    if file is not None:
        context['version'] = file.fileheader.version
    assert 'version' in context
    return context
