from django.core.management.base import BaseCommand
from homepage.models import Division, District, Thana, Area


class Command(BaseCommand):
    help = 'Populate complete Bangladesh location data for checkout'

    def handle(self, *args, **options):
        
        # Create all 8 Divisions of Bangladesh with their districts
        divisions_data = {
            'Dhaka': [
                'Dhaka', 'Faridpur', 'Gazipur', 'Gopalganj', 'Kishoreganj', 'Madaripur', 
                'Manikganj', 'Munshiganj', 'Narayanganj', 'Narsingdi', 'Rajbari', 'Shariatpur', 'Tangail'
            ],
            'Chittagong': [
                'Bandarban', 'Brahmanbaria', 'Chandpur', 'Chittagong', 'Comilla', 
                "Cox's Bazar", 'Feni', 'Khagrachhari', 'Lakshmipur', 'Noakhali', 'Rangamati'
            ],
            'Rajshahi': [
                'Bogura', 'Joypurhat', 'Naogaon', 'Natore', 'Nawabganj', 'Pabna', 
                'Rajshahi', 'Sirajganj'
            ],
            'Rangpur': [
                'Dinajpur', 'Gaibandha', 'Kurigram', 'Lalmonirhat', 'Nilphamari', 
                'Panchagarh', 'Rangpur', 'Thakurgaon'
            ],
            'Khulna': [
                'Bagerhat', 'Chuadanga', 'Jessore', 'Jhenaidah', 'Khulna', 'Kushtia', 
                'Magura', 'Meherpur', 'Narail', 'Satkhira'
            ],
            'Barisal': [
                'Barguna', 'Barisal', 'Bhola', 'Jhalokati', 'Patuakhali', 'Pirojpur'
            ],
            'Sylhet': [
                'Habiganj', 'Moulvibazar', 'Sunamganj', 'Sylhet'
            ],
            'Mymensingh': [
                'Jamalpur', 'Mymensingh', 'Netrokona', 'Sherpur'
            ]
        }
        
        # Create divisions and districts
        for division_name, districts in divisions_data.items():
            division = Division.objects.get_or_create(name=division_name)[0]
            self.stdout.write(f'Created division: {division_name}')
            
            for district_name in districts:
                district = District.objects.get_or_create(name=district_name, division=division)[0]
                self.stdout.write(f'  - Created district: {district_name}')
        
        # Create thanas for major districts only
        major_districts_thanas = {
            'Dhaka': [
                'Adabar', 'Badda', 'Cantonment', 'Darus Salam', 'Dhanmondi', 'Gulshan', 
                'Hazaribagh', 'Kafrul', 'Kalabagan', 'Khilgaon', 'Khilkhet', 'Kotwali', 
                'Lalbagh', 'Mirpur', 'Mohammadpur', 'Motijheel', 'New Market', 'Pallabi', 
                'Ramna', 'Rampura', 'Sabujbagh', 'Shah Ali', 'Shahbagh', 'Sher-e-Bangla Nagar', 
                'Tejgaon', 'Tejgaon I/A', 'Turag', 'Uttara', 'Uttar Khan', 'Wari'
            ],
            'Chittagong': [
                'Akbar Shah', 'Bakalia', 'Bandar', 'Bayazid', 'Chandgaon', 'Chittagong Kotwali', 
                'Double Mooring', 'EPZ', 'Halishahar', 'Karnaphuli', 'Khulshi', 'Pahartali', 
                'Panchlaish', 'Patenga', 'Sadarghat', 'Wari'
            ],
            'Sylhet': [
                'Balaganj', 'Beanibazar', 'Bishwanath', 'Companiganj', 'Dakshin Surma', 
                'Fenchuganj', 'Golapganj', 'Gowainghat', 'Jaintiapur', 'Kanaighat', 
                'Osmani Nagar', 'Sylhet Sadar', 'Zakiganj'
            ],
            'Rajshahi': [
                'Bagha', 'Bagmara', 'Charghat', 'Durgapur', 'Godagari', 'Mohanpur', 
                'Paba', 'Puthia', 'Tanore'
            ]
        }
        
        for district_name, thanas in major_districts_thanas.items():
            try:
                district = District.objects.get(name=district_name)
                for thana_name in thanas:
                    thana = Thana.objects.get_or_create(name=thana_name, district=district)[0]
                    self.stdout.write(f'    - Created thana: {thana_name} in {district_name}')
            except District.DoesNotExist:
                self.stdout.write(f'District {district_name} not found, skipping thanas')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated complete Bangladesh location data!')
        )