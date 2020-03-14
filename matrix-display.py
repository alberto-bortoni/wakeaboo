



/*------------------------------------------------*/

void disp(int tweek, int tday, int thour, int tminute){

  int k;
  int low;
  int hi;
  uint8_t daysAr[2];
  uint8_t timeAr[5];

  if(abs(lastMin-tminute)!=0){
    matrix.clear();

    //display day of week
    daysAr[0] = week[tweek];
    daysAr[1] = daysAr[0];
    matrix.drawBitmap(0, 0, daysAr, 8, 2, LED_ON);


    //number of day
    low = tday%10;
    hi = (tday-low)/10;
    daysAr[0] = daysHi[hi] | daysLow[low];
    daysAr[1] = daysAr[0];
    matrix.drawBitmap(8, 0, daysAr, 8, 2, LED_ON);


    //hours
    low = thour%10;
    hi = (thour-low)/10;

    for(k=0; k<5; k++){
      if(hi!=0){
        timeAr[k] = numbHi[hi][k] | numbLow[low][k];
      }else{
        timeAr[k] = zeros[k] | numbLow[low][k];
      }
    }
    matrix.drawBitmap(0, 3, timeAr, 8, 5, LED_ON);


    //minutes
    low = tminute%10;
    hi = (tminute-low)/10;

    for(k=0; k<5; k++){
      timeAr[k] = numbHi[hi][k] | numbLow[low][k];
    }
    matrix.drawBitmap(8, 3, timeAr, 8, 5, LED_ON);


    matrix.writeDisplay();
  }
}
/*------------------------------------------------*/
















const uint8_t week[] =
  { B11011011,
    B00000011,
    B00011000,
    B00011011,
    B11000000,
    B11000011,
    B11011000,};

const uint8_t daysHi[] =
  { B00000000,
    B00100000,
    B01000000,
    B01100000 };

const uint8_t daysLow[] =
  { B00000000,
    B00000001,
    B00000010,
    B00000011,
    B00000100,
    B00000101,
    B00000110,
    B00000111,
    B00001000,
    B00001001 };

const uint8_t numbLow[10][5] =
{ { B00001110,
    B00001010,
    B00001010,
    B00001010,
    B00001110 },//0
  { B00000010,
    B00000010,
    B00000010,
    B00000010,
    B00000010 },//1
  { B00001110,
    B00000010,
    B00001110,
    B00001000,
    B00001110 },//2
  { B00001110,
    B00000010,
    B00001110,
    B00000010,
    B00001110 },//3
  { B00001010,
    B00001010,
    B00001110,
    B00000010,
    B00000010 },//4
  { B00001110,
    B00001000,
    B00001110,
    B00000010,
    B00001110 },//5
  { B00001110,
    B00001000,
    B00001110,
    B00001010,
    B00001110 },//6
  { B00001110,
    B00000010,
    B00000010,
    B00000010,
    B00000010 },//7
  { B00001110,
    B00001010,
    B00001110,
    B00001010,
    B00001110 },//8
  { B00001110,
    B00001010,
    B00001110,
    B00000010,
    B00000010 }};//9

const uint8_t numbHi[10][5] =
{ { B11100000,
    B10100000,
    B10100000,
    B10100000,
    B11100000 },//0
  { B00100000,
    B00100000,
    B00100000,
    B00100000,
    B00100000 },//1
  { B11100000,
    B00100000,
    B11100000,
    B10000000,
    B11100000 },//2
  { B11100000,
    B00100000,
    B11100000,
    B00100000,
    B11100000 },//3
  { B10100000,
    B10100000,
    B11100000,
    B00100000,
    B00100000 },//4
  { B11100000,
    B10000000,
    B11100000,
    B00100000,
    B11100000 },//5
  { B11100000,
    B10000000,
    B11100000,
    B10100000,
    B11100000 },//6
  { B11100000,
    B00100000,
    B00100000,
    B00100000,
    B00100000 },//7
  { B11100000,
    B10100000,
    B11100000,
    B10100000,
    B11100000 },//8
  { B11100000,
    B10100000,
    B11100000,
    B00100000,
    B00100000 }};//9

const uint8_t zeros[5] =
  { B00000000,
    B00000000,
    B00000000,
    B00000000,
    B00000000 };//0--empty
