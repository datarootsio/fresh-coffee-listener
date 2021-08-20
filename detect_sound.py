from collections import deque
from datetime import datetime
import time
from pathlib import Path
from typing import Union
import os
import logging

import librosa
import numpy as np
import sounddevice as sd
from scipy.spatial import distance
import psycopg2

logging.basicConfig(
    filename="coffee_machine.logs",
    filemode='a',
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    level=20  # INFO
)
logger = logging.getLogger()


class AudioHandler:
    def __init__(self) -> None:
        self.DIST_THRESHOLD = 85
        self.sr = 44100
        self.sec = 0.7
        self.coffee_machine_mfcc, _ = self._set_coffee_machine_features()
        sd.default.device = os.environ["SD_DEFAULT_DEVICE"]

    def start_detection(self) -> None:
        """
        Start listening the environment and if the euclidean distance 3 times less than the threshold
        then count it as coffee machine sound
        """
        logger.info("Listening...")
        logger.info(f"sampling rate: {self.sr}")
        logger.info(sd.query_devices())

        d = deque([500, 500, 500], 3)
        timeout = 12 * 60 * 60  # [seconds]
        timeout_start = time.time()

        while time.time() < timeout_start + timeout:
            sound_record = sd.rec(
                int(self.sec * self.sr),
                samplerate=self.sr,
                channels=1,
                dtype="float32",
                blocking=True,
            ).flatten()

            mfcc_features = self._compute_mean_mfcc(
                sound_record, self.sr
            )
            score = distance.euclidean(self.coffee_machine_mfcc, mfcc_features)
            d.appendleft(score)
            if np.max(d) < self.DIST_THRESHOLD:
                logger.info("coffee machine")
                logger.info(d)
                self.insert_row("coffee")
                time.sleep(43)
                d = deque([500, 500, 500], 3)
                logger.info("start listening again..")
            # print(d)
        logger.info("End of the day, code run successfully ..")

    def _set_coffee_machine_features(self) -> Union[np.array, int]:
        coffee_machine_audio, sr = librosa.load(
            os.environ["COFFEE_AUDIO_PATH"],
            sr=self.sr
        )
        coffee_machine_audio = coffee_machine_audio[:int(self.sec * self.sr)]
        coffee_machine_mfcc = self._compute_mean_mfcc(coffee_machine_audio, sr)
        return coffee_machine_mfcc, sr

    @staticmethod
    def _compute_mean_mfcc(audio, sr, dtype="float32"):
        mfcc_features = librosa.feature.mfcc(audio, sr=sr, dtype=dtype, n_mfcc=20)
        return np.mean(mfcc_features, axis=1)

    @staticmethod
    def insert_row(serving_type):
        connection = None
        cursor = None

        try:
            connection = psycopg2.connect(
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
                host=os.environ["DB_HOST"],
                port=os.environ["DB_PORT"],
                database=os.environ["DB_NAME"]
            )
            cursor = connection.cursor()

            postgres_insert_query = f""" 
                INSERT INTO {os.environ["DB_TABLE"]} (timestamp, office, serving_type) VALUES (%s,%s,%s)
            """
            record_to_insert = (str(datetime.now()), os.environ["OFFICE_NAME"], serving_type)
            cursor.execute(postgres_insert_query, record_to_insert)

            connection.commit()
            count = cursor.rowcount
            logger.info(
                count,
                f"Record inserted successfully into {os.environ['DB_TABLE']} table"
            )

        except (Exception, psycopg2.Error) as error:
            logger.info("Failed to insert record into mobile table", error)
        finally:
            # closing database connection.
            if connection:
                cursor.close()
                connection.close()
                logging.info("PostgreSQL connection is closed")


if __name__ == '__main__':
    AudioHandler().start_detection()
