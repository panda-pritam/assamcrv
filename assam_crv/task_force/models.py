from django.db import models
from village_profile.models import tblVillage 

class TaskForce(models.Model):
    class TeamType(models.TextChoices):
        VLCDMC = "VLCDMC", "VLCDMC"
        SEARCH_RESCUE = "Search & rescue", "Search & rescue"
        RELIEF_MANAGEMENT = "Relief management team", "Relief management team"
        SHELTER_MANAGEMENT = "Shelter Management team", "Shelter Management team"
        FIRST_AID = "First Aid team", "First Aid team"
        WATER_SANITATION = "Water & Sanitation", "Water & Sanitation"

    class PositionResponsibility(models.TextChoices):
        TEAM_MEMBER = "Team member", "Team member"
        TEAM_LEADER = "Team leader", "Team leader"

    village = models.ForeignKey(tblVillage, on_delete=models.CASCADE, related_name="taskforces")
    fullname = models.CharField(max_length=150)
    father_name = models.CharField(max_length=150)
    gender = models.CharField(
        max_length=10,
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")]
    )
    occupation = models.CharField(max_length=150, null=True, blank=True)
    position_responsibility = models.CharField(max_length=50, choices=PositionResponsibility.choices)
    mobile_number = models.CharField(max_length=15)
    team_type = models.CharField(max_length=50, choices=TeamType.choices)

    def __str__(self):
        return f"{self.fullname} - {self.team_type}"
