import kagglehub
import os
import shutil


def link_csv_to(link: str, new_path: str) -> None:
    try:
        # KaggleHub에서 데이터셋 다운로드 시도
        download_path = kagglehub.dataset_download(link)
    except ValueError as e:
        # ValueError를 명시적으로 처리
        if "Invalid dataset handle" in str(e):
            print(f"Error: Invalid dataset handle provided. Please check your link.\n"
                    f"Expected format: 'username/dataset', but got '{link}'")
            return
        else:
            # 다른 ValueError 발생 시 그대로 예외를 재발생
            raise
    except Exception as e:
        # 기타 에러 처리
        print(f"An unexpected error occurred while downloading the dataset: {str(e)}")
        return

    # 새로운 경로 폴더 생성 (exist_ok 지원 없는 경우)
    if not os.path.exists(new_path):
        try:
            os.makedirs(new_path)
        except OSError as e:
            print(f"Error creating directory '{new_path}': {e}")
            return


    try:
        # 다운로드 경로의 모든 파일 이동
        for filename in os.listdir(download_path):
            source_file = os.path.join(download_path, filename)
            destination_file = os.path.join(new_path, filename)
            shutil.move(source_file, destination_file)

        # 원본 폴더 정리
        if not os.listdir(download_path):
            trimmed_path = download_path[:download_path.rfind('/datasets')]
            shutil.rmtree(trimmed_path)  # 상위 폴더 삭제
            print(f"Original directory {trimmed_path+'/datasets'} has been removed.")
        else:
            print(f"Some files still remain in {download_path}. Please check.")
        print("Files saved to: " + new_path + "\n", os.listdir(new_path))

    except Exception as e:
        print(f"Error while moving files: {e}")
