from django.apps import AppConfig


class DjangoCBVInspectConfig(AppConfig):
    name = 'cbv_inspect'

    def ready(self) -> None:
        print("✅✅✅✅✅ HIIIIIII ✅✅✅✅")
        return super().ready()
