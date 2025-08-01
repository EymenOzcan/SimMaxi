from rest_framework import serializers
from .models import Country, eSIMPackage


class eSIMPackageSerializer(serializers.ModelSerializer):
    formatted_name = serializers.SerializerMethodField()

    class Meta:
        model = eSIMPackage
        fields = ["id", "name", "formatted_name", "provider", "price", "data_amount_mb"]

    def get_formatted_name(self, obj):
        if obj.provider.slug == "esimaccess":
            parts = obj.name.split(" ")
            if len(parts) == 3:
                country = parts[0]
                data = parts[1]
                validity = parts[2]
                return f"{country},{validity}/{data}"
            return obj.name

        elif obj.provider.slug == "esimgo":
            parts = obj.name.split(", ")
            if len(parts) >= 5:
                country = parts[3]
                data = parts[1]
                validity = parts[2].replace(" ", " ")
                return f"{country},{validity}/{data}"
            return obj.name

        return obj.name


class CountryEsimSerializer(serializers.ModelSerializer):
    eSIMPackages = eSIMPackageSerializer(
        many=True, read_only=True, source="esimpackage_set"
    )

    class Meta:
        model = Country
        fields = ["name", "code", "eSIMPackages"]
