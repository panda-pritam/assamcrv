from rest_framework import serializers
from .models import FieldImage
from village_profile.models import tblVillage

class FieldImageSerializer(serializers.ModelSerializer):
    village_name = serializers.CharField(source='village.name', read_only=True)
    district_id = serializers.IntegerField(source='village.gram_panchayat.circle.district.id', read_only=True)
    district_name = serializers.CharField(source='village.gram_panchayat.circle.district.name', read_only=True)
    circle_id = serializers.IntegerField(source='village.gram_panchayat.circle.id', read_only=True)
    gram_panchayat_id = serializers.IntegerField(source='village.gram_panchayat.id', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = FieldImage
        fields = [
            'id', 'village', 'village_name', 'district_id', 'circle_id', 'gram_panchayat_id',
            'image', 'image_url', 'upload_datetime', 'category',
            'uploaded_by', 'uploaded_by_name', 'district_name'
        ]
        extra_kwargs = {
            'image': {'write_only': True},
            'uploaded_by': {'read_only': True},
            'name': {'required': False, 'allow_null': True, 'allow_blank': True},  
        }

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

    def validate(self, data):
        village = data.get('village')
        category = data.get('category')
        
        # Count existing images for this village and category
        existing_count = FieldImage.objects.filter(village=village, category=category).count()
        
        # If this is an update operation, don't count the current instance
        if self.instance and self.instance.village == village and self.instance.category == category:
            existing_count -= 1
            
        # Check if we've reached the limit (2 images)
        if existing_count >= 2:
            raise serializers.ValidationError(
                f"Maximum 2 images allowed for {category} in {village.name}. "
                f"Currently there are {existing_count} images."
            )
            
        return data

# class FieldImageSerializer(serializers.ModelSerializer):
#     village_name = serializers.CharField(source='village.name', read_only=True)
#     district_id = serializers.IntegerField(source='village.gram_panchayat.circle.district.id', read_only=True)
#     district_name = serializers.CharField(source='village.gram_panchayat.circle.district.name', read_only=True)
#     circle_id = serializers.IntegerField(source='village.gram_panchayat.circle.id', read_only=True)
#     circle_name = serializers.CharField(source='village.gram_panchayat.circle.name', read_only=True)
#     gram_panchayat_id = serializers.IntegerField(source='village.gram_panchayat.id', read_only=True)
#     gram_panchayat_name = serializers.CharField(source='village.gram_panchayat.name', read_only=True)
#     uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
#     image_url = serializers.SerializerMethodField()

#     class Meta:
#         model = FieldImage
#         fields = [
#             'id', 'village', 'village_name', 
#             'district_id', 'district_name', 
#             'circle_id', 'circle_name',
#             'gram_panchayat_id', 'gram_panchayat_name',
#             'image', 'image_url', 'upload_datetime', 'category',
#             'uploaded_by', 'uploaded_by_name', 'name'
#         ]
#         extra_kwargs = {
#             'image': {'write_only': True},
#             'uploaded_by': {'read_only': True},
#             'name': {'required': False, 'allow_null': True, 'allow_blank': True},  
#         }

#     def get_image_url(self, obj):
#         if obj.image:
#             return self.context['request'].build_absolute_uri(obj.image.url)
#         return None

#     def validate(self, data):
#         village = data.get('village')
#         category = data.get('category')
        
#         # Count existing images for this village and category
#         existing_count = FieldImage.objects.filter(village=village, category=category).count()
        
#         # If this is an update operation, don't count the current instance
#         if self.instance and self.instance.village == village and self.instance.category == category:
#             existing_count -= 1
            
#         # Check if we've reached the limit (2 images)
#         if existing_count >= 2:
#             raise serializers.ValidationError(
#                 f"Maximum 2 images allowed for {category} in {village.name}. "
#                 f"Currently there are {existing_count} images."
#             )
            
#         return data

class BulkFieldImageSerializer(serializers.Serializer):
    village = serializers.PrimaryKeyRelatedField(queryset=tblVillage.objects.all())
    category = serializers.CharField()
    name1 = serializers.CharField(required=False, allow_blank=True)
    name2 = serializers.CharField(required=False, allow_blank=True)
    image1 = serializers.ImageField()
    image2 = serializers.ImageField(required=False)
    
    def validate(self, data):
        village = data.get('village')
        category = data.get('category')
        
        # Count existing images for this village and category
        existing_count = FieldImage.objects.filter(village=village, category=category).count()
        
        # Count how many images we're trying to upload
        upload_count = 1 if data.get('image1') else 0
        if data.get('image2'):
            upload_count += 1
            
        if existing_count + upload_count > 2:
            raise serializers.ValidationError(
                f"Maximum 2 images allowed for {category} in {village.name}. "
                f"Currently there are {existing_count} images. You're trying to upload {upload_count} more."
            )
            
        return data
    
    def create(self, validated_data):
        village = validated_data['village']
        category = validated_data['category']
        user = self.context['request'].user
        
        created_images = []
        
        # Create first image
        if validated_data.get('image1'):
            image1 = FieldImage.objects.create(
                village=village,
                category=category,
                image=validated_data['image1'],
                name=validated_data.get('name1', ''),
                uploaded_by=user
            )
            created_images.append(image1)
        
        # Create second image if provided
        if validated_data.get('image2'):
            image2 = FieldImage.objects.create(
                village=village,
                category=category,
                image=validated_data['image2'],
                name=validated_data.get('name2', ''),
                uploaded_by=user
            )
            created_images.append(image2)
            
        return created_images