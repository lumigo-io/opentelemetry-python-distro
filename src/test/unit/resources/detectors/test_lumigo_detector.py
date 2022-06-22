import lumigo_opentelemetry.resources.detectors as detectors

def test_lumigo_distro_version():
    resource = detectors.LumigoDistroDetector().detect()
    assert 'lumigo.distro.version' in resource.attributes
    assert resource.attributes['lumigo.distro.version']
