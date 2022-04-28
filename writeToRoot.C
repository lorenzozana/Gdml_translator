{
  TFile *MyFile = new TFile("hallB_geant4_dump.root","NEW");
  gSystem->Load("libGeom");
  TGeoManager *geo = new TGeoManager("World", "HallB Geant4");
  geo->Import("output.gdml");
  geo->Write("HallB");
  MyFile->Close();


}
