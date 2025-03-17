from django.core.management.base import BaseCommand
from datetime import datetime
from api.project.models import Project

class Command(BaseCommand):
    help = 'Update existing project codes with current year prefix'

    def handle(self, *args, **kwargs):
        # ✅ Get current year prefix
        current_year_prefix = str(datetime.now().year)[-2:]

        # ✅ Fetch all existing projects where the prefix is old
        projects = Project.objects.exclude(project_code__startswith=current_year_prefix)
        total_projects = projects.count()
        
        # ✅ If no project requires an update, exit
        if total_projects == 0:
            self.stdout.write(self.style.SUCCESS("✅ No project code requires an update."))
            return

        # ✅ Track counters
        updated_count = 0
        failed_count = 0
        failed_projects = []  # Track failed projects

        # ✅ Loop without atomic (no rollback on error)
        for project in projects:
            try:
                # ✅ Extract remaining code after the first 3 digits
                remaining_code = project.project_code[3:].upper()

                # ✅ Generate the new project code with current year prefix
                updated_code = f"{current_year_prefix}{remaining_code}"

                # ✅ Prevent unnecessary updates
                if project.project_code != updated_code:
                    project.project_code = updated_code
                    project.initial_sample_size = project.sample
                    project.save(update_fields=['project_code', 'initial_sample_size'])
                    updated_count += 1

                    # ✅ Log success
                    print(f"✅ Updated Project Code: {project.project_code}")
            except Exception as e:
                failed_count += 1
                failed_projects.append({
                    'project_id': project.id,
                    'project_code': project.project_code,
                    'error': str(e)
                })
                print(f"❌ Failed to update {project.project_code}: {e}")

        # ✅ Write all failed projects in a log file
        if failed_projects:
            with open('failed_projects.log', 'w') as file:
                file.write("Failed Project Updates:\n")
                for failed in failed_projects:
                    file.write(f"Project ID: {failed['project_id']}, Code: {failed['project_code']}, Error: {failed['error']}\n")
            self.stdout.write(self.style.ERROR("❌ All failed projects have been logged to: failed_projects.log"))

        # ✅ Summary Report
        self.stdout.write(self.style.SUCCESS(f"✅ Total Projects: {total_projects}"))
        self.stdout.write(self.style.SUCCESS(f"✅ Successfully Updated: {updated_count}"))
        self.stdout.write(self.style.ERROR(f"❌ Failed Updates: {failed_count}"))
        self.stdout.write(self.style.SUCCESS("🚀 Project Code Update Completed Successfully."))
