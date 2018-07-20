import logging
log = logging.getLogger(__file__)


def main(global_config, **settings):
    """
    this function is the main entry point for Pyramid
    it returns a Pyramid WSGI application
    see setup.py entry points
    """
    from pyramid.config import Configurator

    config = Configurator(settings=settings)

    # logging config for pserve / wsgi
    if settings and 'logging_config_file' in settings:
        from pyramid.paster import setup_logging
        setup_logging(settings['logging_config_file'])

    import views
    views.set_config(settings)

    config.include(views.do_view_config)
    config.scan('ott.services.pyramid')

    return config.make_wsgi_app()
