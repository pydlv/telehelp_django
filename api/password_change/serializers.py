from rest_framework import serializers

from api.util import MySerializer


def password_field():
    return serializers.CharField(min_length=6, style={"input_type": "password"}, write_only=True)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = password_field()
    new_password = password_field()
    confirm_password = password_field()

    def validate_new_password(self, value):
        new_password = self.initial_data["new_password"]
        password_confirm = self.initial_data["confirm_password"]

        if new_password != password_confirm:
            raise serializers.ValidationError({"password": "The passwords must match."})

        return new_password


class RequestPasswordResetSerializer(MySerializer):
    email = serializers.EmailField()


class ResetPasswordFormSerializer(MySerializer):
    email = serializers.EmailField()
    password = password_field()
    confirm_password = password_field()

    token = serializers.CharField(min_length=10)

    def validate_password(self, value):
        new_password = self.initial_data["password"]
        password_confirm = self.initial_data["confirm_password"]

        if new_password != password_confirm:
            raise serializers.ValidationError({"password": "The passwords must match."})

        return new_password
