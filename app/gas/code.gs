/**
 * SCHBC BBMS - Google Apps Script Backend (Production)
 * Railway Cloud 배포용 - 터널 헤더 제거됨
 */

// ==================== 설정 ====================

// FastAPI 백엔드 URL (Railway Production)
const BACKEND_URL = 'https://outstanding-courage.up.railway.app';

// 알람 이메일 수신자
const ADMIN_EMAIL = 'admin@schbc.ac.kr';

// 제제 ID 매핑 (BloodMaster 테이블 기준)
const PREP_IDS = {
  'PRBC': 1,
  'Pre-R': 2,
  'PC': 3,
  'SDP': 4,
  'FFP': 5,
  'Cryo': 6
};

// ==================== 웹 앱 진입점 ====================

/**
 * 웹 앱 접속 시 HTML 페이지 반환
 */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('SCHBC BBMS - 혈액 재고 관리')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// ==================== API 통신 ====================

/**
 * 사용자 로그인
 * @param {Object} credentials - {emp_id, password}
 * @return {Object} 로그인 결과
 */
function loginUser(credentials) {
  try {
    const url = `${BACKEND_URL}/api/auth/login`;
    const options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(credentials),
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(url, options);
    const result = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200) {
      return {
        success: true,
        data: result
      };
    } else {
      return {
        success: false,
        error: result.detail || '로그인 실패'
      };
    }
  } catch (error) {
    Logger.log('Login error: ' + error);
    return {
      success: false,
      error: '서버 연결 실패: ' + error.message
    };
  }
}

/**
 * 재고 데이터 제출
 * @param {Object} formData - 그리드 데이터
 * @return {Object} 제출 결과
 */
function submitData(formData) {
  try {
    const results = [];
    const errors = [];
    
    // 각 혈액형별로 처리
    ['A', 'B', 'O', 'AB'].forEach(bloodType => {
      // 각 제제별로 처리
      Object.keys(PREP_IDS).forEach(prepName => {
        const key = `${bloodType}_${prepName}`;
        const qty = formData[key];
        
        // 값이 있는 경우에만 처리
        if (qty && parseInt(qty) !== 0) {
          const updateData = {
            blood_type: bloodType,
            prep_id: PREP_IDS[prepName],
            in_qty: parseInt(qty) > 0 ? parseInt(qty) : 0,
            out_qty: parseInt(qty) < 0 ? Math.abs(parseInt(qty)) : 0,
            remark: formData.remark || '모바일 입력'
          };
          
          try {
            const url = `${BACKEND_URL}/api/inventory/update`;
            const options = {
              method: 'post',
              contentType: 'application/json',
              payload: JSON.stringify(updateData),
              muteHttpExceptions: true
            };
            
            const response = UrlFetchApp.fetch(url, options);
            const result = JSON.parse(response.getContentText());
            
            if (response.getResponseCode() === 200) {
              // Check if alert email data is returned
              if (result.alert) {
                sendAlertEmail(result.alert);
              }
              
              results.push({
                bloodType: bloodType,
                prep: prepName,
                qty: qty,
                success: true
              });
            } else {
              errors.push({
                bloodType: bloodType,
                prep: prepName,
                error: result.detail || '업데이트 실패'
              });
            }
          } catch (error) {
            errors.push({
              bloodType: bloodType,
              prep: prepName,
              error: error.message
            });
          }
        }
      });
    });
    
    // Note: Alert emails are now sent automatically during update
    // No need to call checkAlerts() separately
    
    return {
      success: errors.length === 0,
      results: results,
      errors: errors,
      message: `${results.length}개 항목 업데이트 완료${errors.length > 0 ? `, ${errors.length}개 실패` : ''}`
    };
    
  } catch (error) {
    Logger.log('Submit error: ' + error);
    return {
      success: false,
      error: '데이터 제출 실패: ' + error.message
    };
  }
}

/**
 * 재고 현황 조회
 * @return {Object} 재고 현황
 */
function getInventoryStatus() {
  try {
    const url = `${BACKEND_URL}/api/inventory/status`;
    const options = {
      method: 'get',
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(url, options);
    const result = JSON.parse(response.getContentText());
    
    if (response.getResponseCode() === 200) {
      return {
        success: true,
        data: result
      };
    } else {
      return {
        success: false,
        error: '재고 조회 실패'
      };
    }
  } catch (error) {
    Logger.log('Get status error: ' + error);
    return {
      success: false,
      error: '서버 연결 실패: ' + error.message
    };
  }
}

// ==================== 이메일 알람 ====================

/**
 * Send alert email using backend-formatted data
 * @param {Object} alertData - {subject, body} from backend
 */
function sendAlertEmail(alertData) {
  try {
    if (!alertData || !alertData.subject || !alertData.body) {
      Logger.log('Invalid alert data');
      return;
    }
    
    GmailApp.sendEmail(
      ADMIN_EMAIL,
      alertData.subject,
      alertData.body
    );
    
    Logger.log(`Alert email sent to ${ADMIN_EMAIL}`);
  } catch (error) {
    Logger.log('Send alert email error: ' + error);
  }
}

/**
 * Manual alert check (for triggers or testing)
 * Note: Alerts are now sent automatically during inventory updates
 */
function manualAlertCheck() {
  // Check all inventory and send alerts if needed
  const statusResult = getInventoryStatus();
  
  if (!statusResult.success) {
    Logger.log('Failed to get inventory status');
    return;
  }
  
  const data = statusResult.data;
  const alertItems = data.items.filter(item => item.is_alert);
  
  if (alertItems.length > 0) {
    // Format and send alert email
    let emailBody = '순천향대학교 부천병원 혈액은행 재고 알림\n\n';
    emailBody += '다음 혈액 제제의 재고가 부족합니다:\n\n';
    
    alertItems.forEach((item, index) => {
      emailBody += `${index + 1}. ${item.blood_type}형 ${item.preparation}: `;
      emailBody += `현재 ${item.current_qty}단위 (알람기준: ${item.alert_threshold}단위)\n`;
    });
    
    emailBody += `\n총 ${alertItems.length}개 항목이 알람 기준 이하입니다.\n`;
    emailBody += `확인 시간: ${new Date().toLocaleString('ko-KR')}\n`;
    
    GmailApp.sendEmail(
      ADMIN_EMAIL,
      '[SCHBC BBMS] 혈액 재고 부족 알람',
      emailBody
    );
    
    Logger.log(`Manual alert sent for ${alertItems.length} items`);
  } else {
    Logger.log('No alerts to send');
  }
}

// ==================== 유틸리티 ====================

/**
 * 백엔드 URL 업데이트 (Railway URL 변경 시 사용)
 * @param {string} newUrl - 새로운 백엔드 URL
 */
function updateBackendUrl(newUrl) {
  // 이 함수는 스크립트 에디터에서 수동으로 실행
  // 실제로는 코드 상단의 BACKEND_URL을 직접 수정해야 함
  Logger.log('Please update BACKEND_URL constant in code.gs to: ' + newUrl);
  return `BACKEND_URL을 다음으로 변경하세요: ${newUrl}`;
}

/**
 * 서버 연결 테스트
 */
function testConnection() {
  try {
    const url = `${BACKEND_URL}/health`;
    const response = UrlFetchApp.fetch(url);
    const result = JSON.parse(response.getContentText());
    
    Logger.log('Connection test successful: ' + JSON.stringify(result));
    return {
      success: true,
      message: '서버 연결 성공',
      data: result
    };
  } catch (error) {
    Logger.log('Connection test failed: ' + error);
    return {
      success: false,
      message: '서버 연결 실패: ' + error.message
    };
  }
}
