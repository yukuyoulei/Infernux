#pragma once

#include <function/resources/AssetRegistry/IAssetLoader.h>
#include <function/resources/InxResource/InxResourceMeta.h>
#include <set>
#include <string>
#include <vector>

namespace infernux
{

class InxScriptSourceLoader : public IAssetLoader
{
  public:
    InxScriptSourceLoader();

    bool LoadMeta(const char *content, const std::string &filePath, InxResourceMeta &metaData) override;
    void CreateMeta(const char *content, size_t contentSize, const std::string &filePath,
                    InxResourceMeta &metaData) override;

    std::shared_ptr<void> Load(const std::string & /*filePath*/, const std::string & /*guid*/,
                               AssetDatabase * /*adb*/) override
    {
        return nullptr;
    }
    bool Reload(std::shared_ptr<void> /*existing*/, const std::string & /*filePath*/, const std::string & /*guid*/,
                AssetDatabase * /*adb*/) override
    {
        return false;
    }
    std::set<std::string> ScanDependencies(const std::string & /*filePath*/, AssetDatabase * /*adb*/) override
    {
        return {};
    }

  private:
    std::string DetectLanguage(const std::string &filePath) const;
    std::set<std::string> ParseImports(const std::string &source, const std::string &language) const;
    std::vector<std::string> ParseClassNames(const std::string &source, const std::string &language) const;
    bool IsInxComponentClass(const std::string &source, const std::string &className, const std::string &language) const;
};

} // namespace infernux
