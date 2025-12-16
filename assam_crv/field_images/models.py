from django.db import models
from django.contrib.auth import get_user_model
from village_profile.models import tblVillage

# Get the custom User model if you have one, otherwise gets the default User model
User = get_user_model()

# Category choices as specified in your requirements
CATEGORY_CHOICES = [
    ('Livelihood', 'Livelihood'),
    ('Educational facilities', 'Educational facilities'),
    ('River bank protection/erosion', 'River bank protection/erosion'),
    ('Infrastructure', 'Infrastructure'),
    ('housing', 'housing'),
    ('PRA and field consultations', 'PRA and field consultations'),
    ('PRA Map', 'PRA Map'),
]

class FieldImage(models.Model):
    """
    Model to store field images with their categories and village associations.
    Ensures maximum 2 images per category per village.
    """
    
    village = models.ForeignKey(
        tblVillage, 
        on_delete=models.CASCADE, 
        related_name='field_images',
        verbose_name="Associated Village"
    )
    
    image = models.ImageField(
        upload_to='field_images/',
        verbose_name="Image File"
    )
    
    upload_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Upload Date & Time"
    )
    
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES,
        verbose_name="Image Category"
    )
    
    name = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        verbose_name="Image Name (Optional)"
    )
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Uploaded By"
    )

    class Meta:
        verbose_name = "Field Image"
        verbose_name_plural = "Field Images"
        ordering = ['-upload_datetime']
        
        # Constraint to ensure max 2 images per category per village
        

    def __str__(self):
        return f"{self.village.name} - {self.get_category_display()} - {self.upload_datetime.date()}"
    
    def save(self, *args, **kwargs):
        """
        Custom save method to enforce the 2-image limit per category per village
        """
        # Count existing images for this village and category
        existing_count = FieldImage.objects.filter(
            village=self.village,
            category=self.category
        ).count()
        
        # If this is an update, don't count the current instance
        if self.pk:
            existing_count -= 1
        
        if existing_count >= 2:
            raise ValueError(f"Maximum 2 images allowed for {self.category} in {self.village.name}")
        
        super().save(*args, **kwargs)