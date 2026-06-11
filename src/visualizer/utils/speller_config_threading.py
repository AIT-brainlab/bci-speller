#Configuration for units=pix
HEIGHT: int = 100
WIDTH: int = 100
UNITS = "pix"
HEIGHT_OF_TARGET = 35
HORI_DIVIDER_START = [-900,0]
HORI_DIVIDER_END = [900,0]
VER_DIVIDER_1_START = [0,500]
ONLINE_VER_DIVIDER_1_START = [0, 400]
VER_DIVIDER_1_END = [0,-500]
DISPLAY_BOX_SIZE = [1700,100]
DISPLAY_BOX_POS = (0,450)
SEQUENCE_POS = ( -140,470)
OUTPUT_POS = (-160,430)

SIZE: int = 100
NUM_BLOCK: int = 2
NUM_TRIAL: int = 2
NUM_SESSION: int = 3
EPOCH_DURATION: float = 2
ITI_DURATION: float = 0.1
CUE_DURATION: float = 1
# For 9 targets: No. of subspeller = 3; No. of Character = 3
# For 16 targets: No. of subspeller = 4; No. of Character = 4
NO_SUBSPELLER: int = 4 # subspeller available n the experiment
NO_CHARACTER: int = 4 # number of characters in each subspellers
NUM_STIMULI: int = NO_SUBSPELLER * NO_CHARACTER
OFFSET_VALUE: int = 1250

###########################
# FREQUENCY
###########################

#9 targets
# FREQS: list = [8, 8, 8, 8.6, 8.6, 8.6, 9, 9, 9]
#16 targets
FREQS: list = [8, 8, 8.6, 8.6, 8, 8, 8.6, 8.6, 9, 9, 9.6, 9.6, 9, 9 ,9.6, 9.6]

###########################
# POSITION
###########################

#9 targets
# POSITIONS: list = [(-800, 200), (0, 200), (800, 200), (-800, 0), (0, 0), (800, 0), (-800, -200), (0, -200), (800, -200)]

#16 targets
POSITIONS: list = [(-800, 300), (-400, 300), (400, 300), (800, 300), 
                   (-800, 100), (-400, 100), (400, 100), (800, 100),
                   (-800, -100), (-400, -100), (400, -100), (800, -100), 
                   (-800,-300), (-400, -300), (400, -300), (800, -300)]

AMPLITUDE: float = 1.0

###########################
# PHASE
###########################

#9 targets
# PHASES: list = [0 , 0 , 0 , 1.05 , 1.05, 1.05, 1.75, 1.75, 1.75]

#16 targets
PHASES: list = [0 , 0 , 1.05 , 1.05, 0 , 0, 1.05 , 1.05 , 1.75 , 1.75, 0.80 , 0.80, 1.75, 1.75, 0.80, 0.80]

###########################
# TARGET CHARACTERS
###########################

#9 targets
# TARGET_CHARACTERS:list = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]

#16 targets
TARGET_CHARACTERS:list = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"]

###########################
# SUBSPELLER DICTIONARY
###########################

#9 targets
# SUBSPELLERS:dict = {"1": ["A", "D", "G"],
#                     "2": ["B", "E", "H"],
#                     "3": ["C", "F", "I"]
#                     }

#16 targets
SUBSPELLERS:dict = {"1": ["A", "B", "E", "F"],
                    "2": ["C", "D", "G", "H"],
                    "3": ["I", "J", "M", "N"],
                    "4": ["K", "L", "O", "P"]
                    }


SERIAL_PORT:str = "COM3"
BOARD_ID:int = -1 #-1 for Synthetic; and 8 for Unicorn. ref.  https://brainflow.readthedocs.io/en/stable/UserAPI.html#brainflow-board-shim
PARTICIPANT_ID:str = "Test_1"
# PARTICIPANT_ID:str="test"
RECORDING_DIR:str = "record_Sub"
TYPE_OF_FILE:str = ".fif"
CSV_DIR:str = "csv/"
BLOCK_BREAK:int = 60
MARKERS:dict = {"A": 1.0, "B": 2.0, "C": 3.0, "D": 4.0, "E": 5.0, "F": 6.0, "G": 7.0, "H": 8.0, "I": 9.0, "J": 10.0, "K": 11.0, "L":12.0, "M": 13.0, "N": 14.0, "O": 15.0, "P":16.0, "trial_start": 99.0}