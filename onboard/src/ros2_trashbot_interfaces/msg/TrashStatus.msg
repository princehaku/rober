# Detected trash status
string frame_id
float64 x
float64 y
float64 z
int8 confidence      # 0-100 detection confidence
int8 trash_type      # 0=unknown, 1=organic, 2=recyclable, 3=general
bool is_bin          # true if this is a trash bin location
float64 timestamp
