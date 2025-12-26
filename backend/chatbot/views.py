
from .agent_service import handle_request 

class ChatView(APIView):
    def post(self, request):
        payload = request.data
        
        # 여기서 'handle_request'를 호출하면
        # 내부적으로 평가 루프가 다 돌아간 뒤의 '최종 결과'만 리턴됩니다.
        response_data = handle_request(payload) 
        
        return Response(response_data)