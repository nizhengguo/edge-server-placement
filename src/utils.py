import copy
import csv
import logging
import os
import pickle
from functools import wraps

from base_station import BaseStation

logging.basicConfig(level=logging.DEBUG)


def memorize(filename):
    """
    装饰器 保存函数运行结果
    :param filename: 缓存文件位置
    
    Example:
        @memorize('cache/square')
        def square(x):
            return x*x
    """

    def _memorize(func):
        @wraps(func)
        def memorized_function(*args, **kwargs):
            if os.path.exists(filename):
                with open(filename, 'rb') as f:
                    cached = pickle.load(f)
                    if isinstance(cached, dict) and cached.get('args', []) == args[:1]:
                        logging.info(
                            msg='Found cache:{0}, {1} does not need to run'.format(filename, func.__name__))
                        return cached['value']
            value = func(*args, **kwargs)
            with open(filename, 'wb') as f:
                cached = {'args': args[:1], 'value': value}
                pickle.dump(cached, f)
            return value

        return memorized_function

    return _memorize


@memorize('cache/base_station')
def base_station_reader(path: str) -> [BaseStation]:
    """
    读取基站经纬度
    
    :param path: csv文件路径, 基站按地址排序
    :return: list of BaseStations
    """
    with open(path, 'r', ) as f:
        reader = csv.reader(f)
        base_stations = []
        count = 0
        for row in reader:
            address = row[0]
            latitude = float(row[1])
            longitude = float(row[2])
            base_stations.append(BaseStation(id=count, addr=address, lat=latitude, lng=longitude))
            logging.debug(
                msg="(Base station:{0}:address={1}, latitude={2}, longitude={3})".format(count, address, latitude,
                                                                                         longitude))
            count += 1
        f.close()
        return base_stations


@memorize('cache/with_user_info')
def user_info_reader(path: str, bs: [BaseStation]) -> [BaseStation]:
    """
    读取用户上网信息
    
    :param path: csv文件路径, 文件应按照基站地址排序
    :param bs: list of BaseStations
    :return: list of BaseStations with user info
    """
    with open(path, 'r') as f:
        reader = csv.reader(f)
        base_stations = []
        count = 0
        last_index = 0
        last_station = None  # type: BaseStation
        next(reader)  # 跳过标题
        for row in reader:
            address = row[4]
            begin_time = row[2]
            end_time = row[3]
            logging.debug(
                msg="(User info:{count}:address={0}, begin_time={1}, end_time={2})".format(address, begin_time,
                                                                                           end_time, count=count))
            if (not last_station) or (not address == last_station.address):
                last_station = None
                for i, item in enumerate(bs[last_index:]):
                    if address == item.address:
                        last_index = i
                        last_station = item
                        base_stations.append(last_station)
                        break
            if last_station:
                last_station.user_num += 1
            count += 1
        f.close()
        return base_stations
