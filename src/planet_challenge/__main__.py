import sys

from planet_challenge.find_best_opportunity import opportunities_pipeline


def main():


    window = 7
    
    if len(sys.argv) > 2:

        start_date = sys.argv[1]

    else:
        start_date = "2024-11-07"
    
    opportunities_pipeline(start_date, window)


if __name__ == "__main__":

    main()