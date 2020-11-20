from rest_framework import parsers, renderers, permissions
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.compat import coreapi, coreschema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.schemas import ManualSchema
from rest_framework.views import APIView

from api.serializers import RegistrationSerializer


class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = [permissions.AllowAny]
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer
    if coreapi is not None and coreschema is not None:
        schema = ManualSchema(
            fields=[
                coreapi.Field(
                    name="email",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Email",
                        description="Valid email for authentication",
                    ),
                ),
                coreapi.Field(
                    name="password",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Password",
                        description="Valid password for authentication",
                    ),
                ),
            ],
            encoding="application/json",
        )

    def post(self, request, *args, **kwargs):
        # TODO: Update all the emails in production to be lower case
        if "username" in request.data:
            request.data["username"] = request.data["username"].lower()

        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            "uuid": user.uuid,
            "account_type": user.account_type
        })


obtain_auth_token = ObtainAuthToken.as_view()


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def registration_view(request):
    if request.method == "POST":
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response({
                "uuid": user.uuid,
                "token": Token.objects.get(user=user).key,
            })
        else:
            return Response(serializer.errors)