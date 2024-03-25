from gplayapi.GoogleAuth import GoogleAuthAPI
from gplayapi.GplayAPI import GplayAPI

# 인증 서비스 생성
auth_service = GoogleAuthAPI(device_profile="<DEVICE_PROFILE>")

# 로그인 호출
auth_service.login(email="<Email>", password="<password>")

# 구글 플레이 서비스 생성
gplay_service = GplayAPI(auth_service)

# 구글 플레이 서비스 사용
details_data = gplay_service.details(package_name="<package_name>")
