<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
  xmlns="http://www.opengis.net/sld"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NamedLayer>
    <Name>Feldwege Laubach</Name>
    <UserStyle>
      <Title>Feldweg-Klassifikation</Title>
      <FeatureTypeStyle>
        
    <Rule>
      <Name>versiegelt</Name>
      <ogc:Filter>
        <ogc:PropertyIsEqualTo>
          <ogc:PropertyName>class_label</ogc:PropertyName>
          <ogc:Literal>versiegelt</ogc:Literal>
        </ogc:PropertyIsEqualTo>
      </ogc:Filter>
      <LineSymbolizer>
        <Stroke>
          <CssParameter name="stroke">#636363</CssParameter>
          <CssParameter name="stroke-width">2</CssParameter>
        </Stroke>
      </LineSymbolizer>
    </Rule>
    <Rule>
      <Name>mineralisch</Name>
      <ogc:Filter>
        <ogc:PropertyIsEqualTo>
          <ogc:PropertyName>class_label</ogc:PropertyName>
          <ogc:Literal>mineralisch</ogc:Literal>
        </ogc:PropertyIsEqualTo>
      </ogc:Filter>
      <LineSymbolizer>
        <Stroke>
          <CssParameter name="stroke">#d7b48b</CssParameter>
          <CssParameter name="stroke-width">2</CssParameter>
        </Stroke>
      </LineSymbolizer>
    </Rule>
    <Rule>
      <Name>begrünt_erdig</Name>
      <ogc:Filter>
        <ogc:PropertyIsEqualTo>
          <ogc:PropertyName>class_label</ogc:PropertyName>
          <ogc:Literal>begrünt_erdig</ogc:Literal>
        </ogc:PropertyIsEqualTo>
      </ogc:Filter>
      <LineSymbolizer>
        <Stroke>
          <CssParameter name="stroke">#74c476</CssParameter>
          <CssParameter name="stroke-width">2</CssParameter>
        </Stroke>
      </LineSymbolizer>
    </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>