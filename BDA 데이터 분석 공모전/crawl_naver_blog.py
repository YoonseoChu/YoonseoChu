import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# 환경에 맞게 경로 설정
CHROMEDRIVER_PATH = "/opt/homebrew/bin/chromedriver"
CHROME_BINARY = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def get_driver():
    options = Options()
    options.binary_location = CHROME_BINARY
    # options.add_argument("--headless=new")  # 봇 감지 방지를 위해 주석 처리
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")  # 자동화 감지 방지
    options.add_experimental_option("excludeSwitches", ["enable-automation"])  # 자동화 표시 제거
    options.add_experimental_option('useAutomationExtension', False)  # 자동화 확장 비활성화
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    
    # 자동화 감지 방지를 위한 스크립트 실행
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def crawl_naver_news(query, max_page=3):
    driver = get_driver()
    news_links = []
    
    try:
        # 1. 네이버 검색 페이지로 이동
        search_url = f"https://search.naver.com/search.naver?query={query}"
        print(f"네이버 검색 페이지로 이동: {search_url}")
        driver.get(search_url)
        time.sleep(5)
        
        # 2. 뉴스 탭 클릭
        print("뉴스 탭 클릭 중...")
        try:
            # 뉴스 탭 찾기 (실제 HTML 구조에 맞는 선택자)
            news_tab_selectors = [
                "a[role='tab'][href*='tab.news']",  # 실제 구조에 맞는 선택자
                "a.tab[href*='tab.news']",
                "a[href*='tab.news']",
                "a[role='tab'] i.ico_nav_news",  # 아이콘을 통한 선택
                "a:contains('뉴스')",
                "a[href*='where=news']",
                "a[data-tab='news']",
                "li a[href*='news']"
            ]
            
            news_tab_found = False
            for selector in news_tab_selectors:
                try:
                    news_tab = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    news_tab.click()
                    news_tab_found = True
                    print(f"뉴스 탭 클릭 성공 (선택자: {selector})")
                    break
                except:
                    continue
            
            if not news_tab_found:
                # 직접 뉴스 검색 URL로 이동
                news_url = f"https://search.naver.com/search.naver?where=news&query={query}"
                print(f"뉴스 탭을 찾을 수 없어 직접 이동: {news_url}")
                driver.get(news_url)
            
            time.sleep(5)
            
        except Exception as e:
            print(f"뉴스 탭 클릭 실패: {e}")
            # 직접 뉴스 검색 URL로 이동
            news_url = f"https://search.naver.com/search.naver?where=news&query={query}"
            print(f"직접 뉴스 검색으로 이동: {news_url}")
            driver.get(news_url)
            time.sleep(5)
        
        # 3. 페이지별 크롤링
        for page in range(1, max_page + 1):
            print(f"\n=== 페이지 {page} 크롤링 시작 ===")
            
            if page > 1:
                # 다음 페이지를 위해 스크롤 다운
                print("다음 페이지 로드를 위해 스크롤 중...")
                for scroll_count in range(3):  # 여러 번 스크롤하여 다음 페이지 로드
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    print(f"스크롤 {scroll_count + 1}/3 완료")
                
                # 페이지 상단으로 이동
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
            
            # 페이지 스크롤하여 모든 콘텐츠 로드
            print("페이지 스크롤 중...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # 검색 결과 로딩 대기
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li.bx, div.total_wrap, div.news_wrap, div.api_subject_bx"))
                )
            except:
                print(f"페이지 {page}에서 검색 결과를 찾을 수 없습니다.")
                continue
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # 디버깅: 페이지의 모든 링크 확인
            print(f"페이지 {page}의 모든 링크 확인:")
            all_links = soup.find_all('a', href=True)
            for i, link in enumerate(all_links[:20], 1):
                href = link.get('href')
                text = link.get_text(strip=True)[:50]
                print(f"  {i}. {href} - {text}")
            
            # 뉴스 링크 수집
            selectors = [
                "li.bx a.title_link",
                "div.total_wrap a.title_link",
                "div.news_wrap a.title_link",
                "a.title_link",
                "li.bx a[href*='news.naver.com']",
                "div.total_wrap a[href*='news.naver.com']",
                "div.news_wrap a[href*='news.naver.com']",
                "a[href*='news.naver.com']"
            ]
            
            page_links = []
            all_found_links = []
            
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    print(f"선택자 '{selector}'로 {len(links)}개 링크 발견")
                    for link in links:
                        href = link.get("href")
                        if href and "news.naver.com" in href:
                            all_found_links.append(href)
                            # 실제 뉴스 링크만 필터링
                            if (href not in page_links and 
                                not href.endswith("/") and
                                len(href) > 30):
                                page_links.append(href)
                    if page_links:
                        break
            
            # 디버깅: 찾은 모든 링크 출력
            if all_found_links:
                print(f"페이지 {page}에서 발견된 모든 뉴스 링크:")
                for i, link in enumerate(all_found_links, 1):
                    print(f"  {i}. {link}")
            
            news_links.extend(page_links)
            print(f"페이지 {page}에서 {len(page_links)}개 뉴스 링크 수집")
            print(f"현재까지 총 {len(news_links)}개 링크 수집됨")
            
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
    
    print(f"\n총 수집된 뉴스 링크 수: {len(news_links)}")

    # 뉴스 내용 수집
    news_data = []
    for i, link in enumerate(news_links):
        try:
            print(f"뉴스 {i+1}/{len(news_links)} 크롤링 중: {link}")
            driver.get(link)
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # 제목 파싱 - 다양한 선택자 시도
            title_selectors = [
                "h1.media_end_head_headline",
                "h2.media_end_head_headline", 
                "h1",
                "h2",
                "title"
            ]
            
            title = "제목 없음"
            for selector in title_selectors:
                title_tag = soup.select_one(selector)
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    if title and title != "제목 없음":
                        break

            # 본문 파싱 - 전체 컨테이너 우선
            content = ""
            # 1. 네이버 뉴스 본문 컨테이너
            container = soup.select_one("div#dic_area")
            if container:
                content = container.get_text(separator=" ", strip=True)
            # 2. 기타 뉴스 본문 컨테이너
            if not content:
                container = soup.select_one("div.article_body")
                if container:
                    content = container.get_text(separator=" ", strip=True)
            # 3. 기존 selector fallback
            if not content:
                content_selectors = [
                    "div#dic_area",
                    "div.article_body",
                    "div.article_content",
                    "div.content",
                    "article"
                ]
                for selector in content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        content = " ".join([c.get_text(strip=True) for c in elements])
                        if content:
                            break
            
            if not content:
                print(f"본문을 찾을 수 없음: {link}")
                continue

            # 언론사 추출
            press_selectors = [
                "a.media_end_head_top_logo",
                "span.media_end_head_top_logo",
                "div.media_end_head_top_logo",
                "a[href*='news.naver.com']"
            ]
            
            press = "언론사 정보 없음"
            for selector in press_selectors:
                press_tag = soup.select_one(selector)
                if press_tag:
                    press = press_tag.get_text(strip=True)
                    if press and press != "언론사 정보 없음":
                        break

            # 키워드 포함 여부
            has_course = any(kw in content for kw in ["코스", "루트", "경로"])
            has_map = any(kw in content for kw in ["지도", "위치", "지점"])

            news_data.append({
                "url": link,
                "title": title,
                "본문": content,  # 전체 본문 저장
                "언론사": press,
                "코스_언급": has_course,
                "지도_언급": has_map
            })
        except Exception as e:
            print(f"오류 발생 ({link}): {e}")

    driver.quit()
    return pd.DataFrame(news_data)

# 실행 예시
if __name__ == "__main__":
    df = crawl_naver_news("런트립", max_page=3)
    print(df.head())
    df.to_csv("naver_news.csv", index=False, encoding="utf-8-sig")
    print("CSV 저장 완료 ✅")