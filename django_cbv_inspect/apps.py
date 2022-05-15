from django.apps import AppConfig


class DjangoCBVInspectConfig(AppConfig):
    name = 'django_cbv_inspect'

    def ready(self) -> None:
        print("✅✅✅✅✅ HIIIIIII ✅✅✅✅")
        return super().ready()
