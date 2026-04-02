#include "InxScriptSourceLoader.hpp"

#include <algorithm>
#include <core/log/InxLog.h>
#include <filesystem>
#include <platform/filesystem/InxPath.h>
#include <regex>
#include <sstream>

namespace infernux
{

InxScriptSourceLoader::InxScriptSourceLoader()
{
    INXLOG_DEBUG("InxScriptSourceLoader initialized");
}

bool InxScriptSourceLoader::LoadMeta(const char * /*content*/, const std::string &filePath, InxResourceMeta &metaData)
{
    std::string metaPath = InxResourceMeta::GetMetaFilePath(filePath);
    if (std::filesystem::exists(ToFsPath(metaPath))) {
        return metaData.LoadFromFile(metaPath);
    }
    return false;
}

void InxScriptSourceLoader::CreateMeta(const char *content, size_t contentSize, const std::string &filePath,
                                       InxResourceMeta &metaData)
{
    const std::string language = DetectLanguage(filePath);
    INXLOG_DEBUG("Creating metadata for script source: ", filePath, " language=", language);

    metaData.Init(content, contentSize, filePath, ResourceType::Script);

    std::filesystem::path path = ToFsPath(filePath);
    std::string extension = path.extension().string();
    std::string contentStr;
    if (content && contentSize > 0) {
        contentStr.assign(content, contentSize);
    }

    metaData.AddMetadata("file_type", std::string("script"));
    metaData.AddMetadata("file_extension", extension);
    metaData.AddMetadata("language", language);

    size_t lineCount = std::count(contentStr.begin(), contentStr.end(), '\n') + 1;
    metaData.AddMetadata("line_count", lineCount);

    std::set<std::string> imports = ParseImports(contentStr, language);
    std::string importsStr;
    for (const auto &imp : imports) {
        if (!importsStr.empty())
            importsStr += ",";
        importsStr += imp;
    }
    metaData.AddMetadata("imports", importsStr);

    std::vector<std::string> classNames = ParseClassNames(contentStr, language);
    std::string classesStr;
    std::string componentClassesStr;
    for (const auto &cls : classNames) {
        if (!classesStr.empty())
            classesStr += ",";
        classesStr += cls;

        if (IsInxComponentClass(contentStr, cls, language)) {
            if (!componentClassesStr.empty())
                componentClassesStr += ",";
            componentClassesStr += cls;
        }
    }
    metaData.AddMetadata("classes", classesStr);
    metaData.AddMetadata("component_classes", componentClassesStr);
    metaData.AddMetadata("has_components", !componentClassesStr.empty());

    try {
        if (std::filesystem::exists(path)) {
            metaData.AddMetadata("file_size", static_cast<size_t>(std::filesystem::file_size(path)));
        }
    } catch (const std::filesystem::filesystem_error &e) {
        INXLOG_ERROR("Failed to get file size for ", filePath, " : ", e.what());
    }
}

std::string InxScriptSourceLoader::DetectLanguage(const std::string &filePath) const
{
    const std::string ext = ToFsPath(filePath).extension().string();
    if (ext == ".cs")
        return "csharp";
    if (ext == ".py" || ext == ".pyc")
        return "python";
    return "script";
}

std::set<std::string> InxScriptSourceLoader::ParseImports(const std::string &source, const std::string &language) const
{
    std::set<std::string> imports;
    std::istringstream stream(source);
    std::string line;
    const std::regex importRegex(
        language == "csharp" ? R"(^\s*using\s+([a-zA-Z_][a-zA-Z0-9_.]*))"
                             : R"(^\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_.]*))");

    while (std::getline(stream, line)) {
        std::smatch match;
        if (std::regex_search(line, match, importRegex) && match.size() > 1) {
            std::string moduleName = match[1].str();
            const size_t dotPos = moduleName.find('.');
            if (dotPos != std::string::npos) {
                moduleName = moduleName.substr(0, dotPos);
            }
            imports.insert(moduleName);
        }
    }
    return imports;
}

std::vector<std::string> InxScriptSourceLoader::ParseClassNames(const std::string &source,
                                                                const std::string &language) const
{
    std::vector<std::string> classNames;
    std::istringstream stream(source);
    std::string line;
    const std::regex classRegex(
        language == "csharp"
            ? R"(^\s*(?:(?:public|internal|protected|private|abstract|sealed|static|partial)\s+)*class\s+([a-zA-Z_][a-zA-Z0-9_]*))"
            : R"(^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*))");

    while (std::getline(stream, line)) {
        std::smatch match;
        if (std::regex_search(line, match, classRegex) && match.size() > 1) {
            classNames.push_back(match[1].str());
        }
    }
    return classNames;
}

bool InxScriptSourceLoader::IsInxComponentClass(const std::string &source, const std::string &className,
                                                const std::string &language) const
{
    const std::string pattern =
        language == "csharp" ? (R"(class\s+)" + className + R"(\s*:\s*[^{\n]*\bInxComponent\b)")
                             : (R"(class\s+)" + className + R"(\s*\([^)]*InxComponent[^)]*\))");
    std::regex componentRegex(pattern);
    if (std::regex_search(source, componentRegex)) {
        return true;
    }

    if (language == "python") {
        std::string parentPattern = R"(class\s+)" + className + R"(\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\))";
        std::regex parentRegex(parentPattern);
        std::smatch match;
        if (std::regex_search(source, match, parentRegex) && match.size() > 1) {
            std::string parentClass = match[1].str();
            if (parentClass.length() > 9 && parentClass.substr(parentClass.length() - 9) == "Component") {
                return true;
            }
        }
    }

    return false;
}

} // namespace infernux
