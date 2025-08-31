"""
AI Species Identification Prompt Configuration

This file contains the prompt template used for AI species identification.
Users can customize this prompt to match their specific geographic location,
local wildlife species, and research needs.

Variables available for use in the prompt:
- {location}: Camera trap location (from CAMERA_TRAP_LOCATION in .env)
- {location_upper}: Camera trap location in uppercase
- {region}: Geographic region (from CAMERA_TRAP_REGION in .env)
"""

# Main AI prompt template
# You can customize this entire prompt to match your location and species
AI_PROMPT_TEMPLATE = """Analyze this camera trap image crop from {location_upper} and identify any animals present.

IMPORTANT CONTEXT: This image is from a camera trap in {location}, so focus specifically on wildlife species native to or commonly found in {region} ecosystems including:

LARGE MAMMALS: African elephant, black rhinoceros, white rhinoceros, giraffe, hippopotamus, African buffalo, lion, leopard, cheetah, spotted hyena, brown hyena, African wild dog

ANTELOPES & UNGULATES: Gemsbok (oryx), springbok, kudu, eland, impala, steenbok, klipspringer, red hartebeest, blue wildebeest, waterbuck, reedbuck, duiker species

SMALLER MAMMALS: Warthog, bushpig, aardvark, pangolin, caracal, serval, African wildcat, black-backed jackal, bat-eared fox, cape fox, honey badger, various mongoose species

BIRDS: Ostrich, secretary bird, various ground-dwelling species that might trigger camera traps

Please provide:
1. Species name (common and scientific name)
2. Confidence level (High/Medium/Low) - be more confident if it matches known {region} species
3. Count of individuals visible
4. Brief description including behavior/posture
5. Habitat context if visible (desert, savanna, woodland, etc.)

If uncertain between similar species, mention the most likely candidates for {location}. If no animals are clearly visible, indicate that.

Format your response as JSON with keys: species, scientific_name, confidence, count, description, habitat"""

# Alternative prompt templates for different regions
# Users can uncomment and modify these, or create their own

# NORTH_AMERICA_PROMPT = """Analyze this camera trap image from {location} and identify any animals present.
# 
# Focus on North American wildlife including:
# LARGE MAMMALS: White-tailed deer, mule deer, elk, moose, black bear, brown bear, mountain lion, bobcat, coyote, wolf
# SMALLER MAMMALS: Raccoon, opossum, skunk, porcupine, beaver, otter, fox species, various rodents
# BIRDS: Wild turkey, various ground birds that trigger camera traps
# 
# Please provide species identification with confidence level and count."""

# EUROPE_PROMPT = """Analyze this camera trap image from {location} and identify any animals present.
# 
# Focus on European wildlife including:
# LARGE MAMMALS: Red deer, roe deer, wild boar, brown bear, wolf, lynx, fox
# SMALLER MAMMALS: Badger, pine marten, various mustelids, rodent species
# BIRDS: Various ground-dwelling species
# 
# Please provide species identification with confidence level and count."""

# ASIA_PROMPT = """Analyze this camera trap image from {location} and identify any animals present.
# 
# Focus on Asian wildlife (customize based on specific country/region):
# LARGE MAMMALS: Tiger, leopard, Asian elephant, various deer species, wild boar, bears
# SMALLER MAMMALS: Various cats, civets, mongooses, primates
# 
# Please provide species identification with confidence level and count."""

# Instructions for customization:
# 1. Edit AI_PROMPT_TEMPLATE above to match your location's wildlife
# 2. Replace the species lists with animals found in your area
# 3. Adjust the confidence criteria and habitat types
# 4. Use {location}, {location_upper}, and {region} variables as needed
# 5. You can also create entirely new prompt templates
# 6. Save this file after making changes - no restart required!

# Example of variable usage:
# {location} = "Namibia, Africa" 
# {location_upper} = "NAMIBIA, AFRICA"
# {region} = "Southern Africa"